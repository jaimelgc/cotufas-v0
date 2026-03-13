"""
python manage.py load_cinema_data data/merged.json
python manage.py load_cinema_data data/merged.json --clear
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from movies.models import Movie, Showing, Theater


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

        # Clear existing data if requested
        if options['clear']:
            self.stdout.write(self.style.WARNING('🗑️  Clearing existing data...'))
            Showing.objects.all().delete()
            Movie.objects.all().delete()
            # Don't delete theaters - they have pricing config
            self.stdout.write('   Cleared showings and movies')

        # Load JSON data
        self.stdout.write(f'\n📂 Loading data from {json_file}...')
        with open(json_file, 'r', encoding='utf-8') as f:
            movies_data = json.load(f)

        self.stdout.write(f'   Found {len(movies_data)} movies\n')

        # Setup theaters with pricing if requested
        if options['update_pricing']:
            self.setup_theaters()

        # Load movies and showings
        stats = self.load_movies(movies_data)

        # Print statistics
        self.print_statistics(stats)

        self.stdout.write(self.style.SUCCESS('\n✅ Data loading complete!'))

    def setup_theaters(self):
        """Create/update theaters with pricing information"""
        self.stdout.write('🎭 Setting up theaters with pricing...')

        # Define theater pricing
        # TODO: Customize these prices based on actual theater pricing
        theater_configs = {
            'yelmo la villa': {
                'location': 'Centro Comercial La Villa, TF-5, s/n, 38300 La Orotava, Santa Cruz de Tenerife',
                'base_prices': {'weekday': 10.70, 'wednesday': 7.40},
            },
            'yelmo meridiano': {
                'location': 'Av. Manuel Hermoso Rojas, 16, 38005 Santa Cruz de Tenerife',
                'base_prices': {'weekday': 10.70, 'wednesday': 7.40},
            },
            'xsur': {
                'location': 'X-Sur, C. Lisboa, centro comercial, 38660 Costa Adeje, Santa Cruz de Tenerife',
                'base_prices': {'weekday': 6.50, 'weekend': 8.00, 'holiday': 8.50},
            },
            'multicines': {
                'location': 'CC ALCAMPO, CAMINO DE LA HORNERA S/N. CC ALCAMPO LA LAGUNA, Cam. la Hornera, S/N, 38296 La Laguna, Santa Cruz de Tenerife',
                'base_prices': {'weekday': 7.00, 'weekend': 8.50, 'holiday': 9.00},
            },
            'zentralcenter': {
                'location': 'Centro Comercial Zentral Center, Av. Arquitecto Gómez Cuesta, 22, 38650 Arona, Santa Cruz de Tenerife',
                'base_prices': {'weekday': 6.00, 'weekend': 7.50, 'holiday': 8.00},
            },
        }

        for name, config in theater_configs.items():
            theater, created = Theater.objects.update_or_create(
                name=name,
                defaults={
                    'location': config['location'],
                    'base_prices': config['base_prices'],
                    'format_surcharges': config['format_surcharges'],
                },
            )
            action = 'Created' if created else 'Updated'
            self.stdout.write(f'   {action} theater: {name}')

        self.stdout.write('')

    @transaction.atomic
    def load_movies(self, movies_data: list) -> Dict[str, int]:
        """
        Load movies and showings from JSON data

        Returns:
            Statistics dictionary
        """
        stats = {
            'movies_created': 0,
            'movies_updated': 0,
            'showings_created': 0,
            'showings_skipped': 0,
            'theaters_missing': set(),
        }

        for i, movie_data in enumerate(movies_data, 1):
            # Progress indicator
            if i % 10 == 0:
                self.stdout.write(f'   Processing movie {i}/{len(movies_data)}...')

            try:
                movie_stats = self.load_movie(movie_data)

                # Aggregate stats
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

    def load_movie(self, movie_data: Dict[str, Any]) -> Dict[str, Any]:
        """Load a single movie and its showings"""

        # Create or update movie
        movie, created = Movie.objects.update_or_create(
            title=movie_data['title'],
            defaults={
                'length': movie_data.get('length'),
                'age': movie_data.get('age', '0'),
                'actors': movie_data.get('actors') or [],
                'directors': movie_data.get('directors') or [],
                'producers': movie_data.get('producers') or [],
                'genres': movie_data.get('genres') or [],
                'synopsis': movie_data.get('synopsis'),
                'all_synopsis': movie_data.get('all_synopsis') or {},
                'url': movie_data.get('url'),
                'all_urls': movie_data.get('all_urls') or {},
            },
        )

        movie_stats = {
            'created': created,
            'showings_created': 0,
            'showings_skipped': 0,
            'theaters_missing': set(),
        }

        # Load showings
        for showing_data in movie_data.get('showings', []):
            showing_stats = self.load_showing(movie, showing_data)
            movie_stats['showings_created'] += showing_stats['created']
            movie_stats['showings_skipped'] += showing_stats['skipped']
            if showing_stats['theater_missing']:
                movie_stats['theaters_missing'].add(showing_stats['theater_missing'])

        return movie_stats

    def load_showing(self, movie: Movie, showing_data: Dict[str, Any]) -> Dict[str, Any]:
        """Load a single showing"""

        theater_name = showing_data['theater']

        # Get theater
        try:
            theater = Theater.objects.get(name=theater_name)
        except Theater.DoesNotExist:
            # Create theater without pricing (can be updated later)
            theater = Theater.objects.create(name=theater_name, location='Unknown')
            return {'created': 0, 'skipped': 0, 'theater_missing': theater_name}

        # Parse date and time
        try:
            date = self.parse_date(showing_data['date'])
            time = self.parse_time(showing_data['time'])
        except (ValueError, KeyError) as e:
            self.stdout.write(
                self.style.WARNING(f'   ⚠️  Could not parse date/time for {movie.title}: {e}')
            )
            return {'created': 0, 'skipped': 1, 'theater_missing': None}

        # Skip past showings
        if date < timezone.now().date():
            return {'created': 0, 'skipped': 1, 'theater_missing': None}

        # Create or get showing
        showing, created = Showing.objects.get_or_create(
            movie=movie,
            theater=theater,
            date=date,
            time=time,
            cinema=showing_data.get('cinema'),
            format=showing_data.get('format'),
        )

        return {
            'created': 1 if created else 0,
            'skipped': 0 if created else 1,
            'theater_missing': None,
        }

    def parse_date(self, date_str: str) -> datetime.date:
        """Parse date string (YYYY-MM-DD)"""
        return datetime.strptime(date_str, '%Y-%m-%d').date()

    def parse_time(self, time_str: str) -> datetime.time:
        """Parse time string (HH:MM)"""
        return datetime.strptime(time_str, '%H:%M').time()

    def print_statistics(self, stats: Dict[str, Any]):
        """Print loading statistics"""
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

        # Database totals
        self.stdout.write('\n📈 Database Totals:')
        self.stdout.write(f'   Theaters: {Theater.objects.count()}')
        self.stdout.write(f'   Movies: {Movie.objects.count()}')
        self.stdout.write(f'   Showings: {Showing.objects.count()}')

        self.stdout.write('=' * 60)
