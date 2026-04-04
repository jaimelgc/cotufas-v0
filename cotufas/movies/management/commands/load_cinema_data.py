"""
python manage.py load_cinema_data movies/data/merged.json
python manage.py load_cinema_data movies/data/merged.json --clear
python manage.py load_cinema_data movies/data/merged.json --update-pricing
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify

from ...models import Movie, Showing, Theater

THEATER_CINEMA_MAP = {
    'yelmo-meridiano': 'yelmo-meridiano',
    'yelmo-la-villa-de-orotava': 'yelmo-la-villa',
    'multicines': 'multicines',
    'xsur': 'xsur',
    'zentralcenter': 'zentralcenter',
}


class Command(BaseCommand):
    help = 'Load cinema data from merged JSON file'

    def add_arguments(self, parser):
        parser.add_argument(
            'json_file', type=str, help='Path to merged JSON file (e.g., data/merged.json)'
        )
        parser.add_argument(
            '--clear', action='store_true', help='Clear existing data before loading'
        )
        parser.add_argument(
            '--update-pricing', action='store_true', help='Update theater pricing information'
        )

    def handle(self, *args, **options):
        json_file = Path(options['json_file'])

        if not json_file.exists():
            raise CommandError(f'File not found: {json_file}')

        if options['clear']:
            self.stdout.write(self.style.WARNING('🗑️  Clearing existing data...'))
            Showing.objects.all().delete()
            Movie.objects.all().delete()
            self.stdout.write('   Cleared showings and movies')

        self.stdout.write(f'\n📂 Loading data from {json_file}...')
        with open(json_file, 'r', encoding='utf-8') as f:
            movies_data = json.load(f)

        self.stdout.write(f'   Found {len(movies_data)} movies\n')

        self.setup_theaters(force_update=options['update_pricing'])

        stats = self.load_movies(movies_data)
        self.print_statistics(stats)
        self.stdout.write(self.style.SUCCESS('\n✅ Data loading complete!'))

    def setup_theaters(self, force_update: bool = False):
        """Create theaters (always) and update pricing (only when force_update=True or new)"""
        self.stdout.write('🎭 Setting up theaters...')

        yelmo_prices = {'weekday': 10.7, 'wednesday': 7.4}

        theater_configs = {
            'yelmo-meridiano': {
                'name': 'yelmo meridiano',
                'location': 'Av. Manuel Hermoso Rojas, 16, 38005 Santa Cruz de Tenerife',
                'city': 'Santa Cruz de Tenerife',
                'base_prices': yelmo_prices,
                'website': 'https://yelmocines.es/cartelera/santa-cruz-tenerife/meridiano',
            },
            'yelmo-la-villa': {
                'name': 'yelmo la villa',
                'location': 'Centro Comercial La Villa, TF-5, s/n, 38300 La Orotava, Santa Cruz de Tenerife',
                'city': 'La Orotava',
                'base_prices': yelmo_prices,
                'website': 'https://yelmocines.es/cartelera/santa-cruz-tenerife/la-villa-de-orotava',
            },
            'xsur': {
                'name': 'xsur',
                'location': 'X-Sur, C. Lisboa, centro comercial, 38660 Costa Adeje, Santa Cruz de Tenerife',
                'city': 'Costa Adeje',
                'base_prices': {'weekday': 5.5},
                'website': 'https://x-surcine.com/',
            },
            'multicines': {
                'name': 'multicines',
                'location': 'CC ALCAMPO, Cam. la Hornera, S/N, 38296 La Laguna, Santa Cruz de Tenerife',
                'city': 'La Laguna',
                'base_prices': {'weekday': 7.9, 'reduced': 7.2, 'wednesday': 5.5},
                'website': 'https://multicinestenerife.com/',
            },
            'zentralcenter': {
                'name': 'zentralcenter',
                'location': 'Centro Comercial Zentral Center, Av. Arquitecto Gómez Cuesta, 22, 38650 Arona, Santa Cruz de Tenerife',
                'city': 'Arona',
                'base_prices': {'weekday': 5},
                'website': 'https://cinezentralcenter.com/',
            },
        }

        for slug, config in theater_configs.items():
            existing = Theater.objects.filter(slug=slug).first()
            if existing and not force_update:
                # Theater already exists with real data; don't overwrite it
                self.stdout.write(f'   Skipped (already configured): {slug}')
                continue

            theater, created = Theater.objects.update_or_create(
                slug=slug,
                defaults={
                    'name': config['name'],
                    'location': config['location'],
                    'city': config['city'],
                    'base_prices': config['base_prices'],
                    'website': config['website'],
                },
            )
            action = 'Created' if created else 'Updated'
            self.stdout.write(f'   {action} theater: {slug}')

        self.stdout.write('')

    @transaction.atomic
    def load_movies(self, movies_data: list) -> Dict[str, int]:
        stats = {
            'movies_created': 0,
            'movies_updated': 0,
            'showings_created': 0,
            'showings_skipped': 0,
            'theaters_missing': set(),
        }

        for i, movie_data in enumerate(movies_data, 1):
            if i % 10 == 0:
                self.stdout.write(f'   Processing movie {i}/{len(movies_data)}...')

            try:
                movie_stats = self.load_movie(movie_data)

                if movie_stats['created']:
                    stats['movies_created'] += 1
                else:
                    stats['movies_updated'] += 1

                stats['showings_created'] += movie_stats['showings_created']
                stats['showings_skipped'] += movie_stats['showings_skipped']
                stats['theaters_missing'].update(movie_stats['theaters_missing'])

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'   ❌ Error loading {movie_data.get("title")}: {e}')
                )
                continue

        return stats

    def _unique_slug(self, base_slug: str, title: str) -> str:
        """
        Return base_slug if no other movie uses it (or the one that does
        is the same title).  Otherwise append -2, -3, … until unique.
        """
        qs = Movie.objects.filter(slug=base_slug).exclude(title=title)
        if not qs.exists():
            return base_slug
        counter = 2
        while Movie.objects.filter(slug=f"{base_slug}-{counter}").exclude(title=title).exists():
            counter += 1
        return f"{base_slug}-{counter}"

    def load_movie(self, movie_data: Dict[str, Any]) -> Dict[str, Any]:
        """Load a single movie and its showings"""
        base_slug = slugify(movie_data['title'])
        slug = self._unique_slug(base_slug, movie_data['title'])

        movie, created = Movie.objects.update_or_create(
            title=movie_data['title'],
            defaults={
                'slug': slug,
                'length': movie_data.get('length'),
                'age': movie_data.get('age', '0'),
                'theaters': movie_data.get('theaters') or [],
                'actors': movie_data.get('actors') or [],
                'directors': movie_data.get('directors') or [],
                'producers': movie_data.get('producers') or [],
                'genres': movie_data.get('genres') or [],
                'synopsis': movie_data.get('synopsis'),
                'all_synopsis': movie_data.get('all_synopsis') or {},
                'all_urls': movie_data.get('all_urls') or {},
            },
        )

        movie_stats = {
            'created': created,
            'showings_created': 0,
            'showings_skipped': 0,
            'theaters_missing': set(),
        }

        for showing_data in movie_data.get('showings', []):
            showing_stats = self.load_showing(movie, showing_data)
            movie_stats['showings_created'] += showing_stats['created']
            movie_stats['showings_skipped'] += showing_stats['skipped']
            if showing_stats['theater_missing']:
                movie_stats['theaters_missing'].add(showing_stats['theater_missing'])

        return movie_stats

    def resolve_theater(self, theater_name: str, cinema: str | None) -> Theater | None:
        slug = THEATER_CINEMA_MAP.get(theater_name)
        if slug is None:
            return None
        try:
            return Theater.objects.get(slug=slug)
        except Theater.DoesNotExist:
            return None

    def load_showing(self, movie: Movie, showing_data: Dict[str, Any]) -> Dict[str, Any]:
        """Load a single showing"""
        theater_name = showing_data['theater']
        cinema = showing_data.get('cinema')

        theater = self.resolve_theater(theater_name, cinema)

        if theater is None:
            # Create a minimal theater so data isn't lost; pricing can be added later.
            key = f"{theater_name}-{cinema}" if cinema else theater_name
            theater, _ = Theater.objects.get_or_create(
                slug=key,
                defaults={'name': key, 'location': 'Unknown', 'city': 'Unknown'},
            )
            return {'created': 0, 'skipped': 0, 'theater_missing': key}

        try:
            date = self.parse_date(showing_data['date'])
            time = self.parse_time(showing_data['time'])
        except (ValueError, KeyError) as e:
            self.stdout.write(
                self.style.WARNING(f'   ⚠️  Could not parse date/time for {movie.title}: {e}')
            )
            return {'created': 0, 'skipped': 1, 'theater_missing': None}

        if date < timezone.now().date():
            return {'created': 0, 'skipped': 1, 'theater_missing': None}

        showing, created = Showing.objects.get_or_create(
            movie=movie,
            theater=theater,
            date=date,
            time=time,
            format=showing_data.get('format'),
        )

        return {
            'created': 1 if created else 0,
            'skipped': 0 if created else 1,
            'theater_missing': None,
        }

    def parse_date(self, date_str: str) -> datetime.date:
        return datetime.strptime(date_str, '%Y-%m-%d').date()

    def parse_time(self, time_str: str) -> datetime.time:
        return datetime.strptime(time_str, '%H:%M').time()

    def print_statistics(self, stats: Dict[str, Any]):
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write('📊 LOADING STATISTICS')
        self.stdout.write('=' * 60)

        self.stdout.write('\n🎬 Movies:')
        self.stdout.write(f'   Created: {stats["movies_created"]}')
        self.stdout.write(f'   Updated: {stats["movies_updated"]}')

        self.stdout.write('\n🎟️  Showings:')
        self.stdout.write(f'   Created: {stats["showings_created"]}')
        self.stdout.write(f'   Skipped: {stats["showings_skipped"]} (duplicates or past dates)')

        if stats['theaters_missing']:
            self.stdout.write(
                self.style.WARNING(
                    f'\n⚠️  Theaters created without pricing: {", ".join(stats["theaters_missing"])}'
                )
            )
            self.stdout.write('   Run with --update-pricing to add pricing info')

        self.stdout.write('\n📈 Database Totals:')
        self.stdout.write(f'   Theaters: {Theater.objects.count()}')
        self.stdout.write(f'   Movies: {Movie.objects.count()}')
        self.stdout.write(f'   Showings: {Showing.objects.count()}')
        self.stdout.write('=' * 60)
        self.stdout.write('=' * 60)
