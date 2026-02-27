"""
Cinema Data Normalization Pipeline
====================================

This module normalizes raw JSON data from different cinema scrapers into a unified format.

Target Schema:
{
    "title": str,
    "length": str,
    "age": str | null,
    "theater": str,
    "showings": {
        "YYYY-MM-DD": ["HH:MM", ...],
        ...
    },
    "actors": [str, ...] | null,
    "directors": [str, ...] | null,
    "genres": [str, ...] | null,
    "synopsis": str | null,
    "url": str | null
}
"""

import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class CinemaNormalizer:
    """Base class for normalizing cinema data"""

    def __init__(self, input_path: str, output_path: str):
        self.input_path = Path(input_path)
        self.output_path = Path(output_path)

    def load_data(self) -> List[Dict[str, Any]]:
        """Load JSON data from input file"""
        with open(self.input_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def save_data(self, data: List[Dict[str, Any]], indent: int = 2) -> None:
        """Save normalized data to output file with pretty printing"""
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=indent)
        print(f"Saved {len(data)} movies to {self.output_path}")

    def normalize(self) -> List[Dict[str, Any]]:
        """Override this method in subclasses"""
        raise NotImplementedError


class YelmoNormalizer(CinemaNormalizer):
    """Normalize Yelmo cinema data"""

    @staticmethod
    def convert_timestamp_to_date(timestamp: str) -> str:
        """Convert timestamp format to YYYY-MM-DD"""
        # The timestamp is in .NET ticks (100-nanosecond intervals since 0001-01-01)
        try:
            ticks = int(timestamp)
            # Convert .NET ticks to Unix timestamp
            # .NET epoch is 0001-01-01, Unix epoch is 1970-01-01
            # Difference is 621355968000000000 ticks
            unix_ticks = ticks - 621355968000000000
            unix_seconds = unix_ticks / 10000000
            dt = datetime.fromtimestamp(unix_seconds)
            return dt.strftime('%Y-%m-%d')
        except (ValueError, OSError):
            return timestamp

    def normalize(self) -> List[Dict[str, Any]]:
        """
        Transform Yelmo data structure:
        - Flatten nested theater/format structure
        - Convert timestamps to readable dates
        - Merge multiple showings per movie
        """
        raw_data = self.load_data()

        # Group movies by title (they may appear multiple times)
        movies_by_title: Dict[str, Dict[str, Any]] = {}

        for item in raw_data:
            detail = item['detail']
            title = detail['title']
            theater = item['theater']

            # Initialize movie entry if first time seeing this title
            if title not in movies_by_title:
                movies_by_title[title] = {
                    'title': title,
                    'length': detail.get('length'),
                    'age': detail.get('age'),
                    'theater': theater,
                    'showings': {},
                    'actors': detail.get('details', {}).get('Actores:'),
                    'directors': detail.get('details', {}).get('Directores:'),
                    'producers': detail.get('details', {}).get('Productores:'),
                    'genres': [detail.get('genres')] if detail.get('genres') else None,
                    'synopsis': detail.get('synopsis'),
                    'url': detail.get('url'),
                }

            # Merge showings from all theaters/formats
            for cinema_name, formats in item['showings'].items():
                for format_name, dates in formats.items():
                    for timestamp, times in dates.items():
                        date = self.convert_timestamp_to_date(timestamp)

                        # Add cinema and format info to the showing
                        showing_key = f"{date} ({cinema_name} - {format_name})"

                        if showing_key not in movies_by_title[title]['showings']:
                            movies_by_title[title]['showings'][showing_key] = []

                        movies_by_title[title]['showings'][showing_key].extend(times)

        # Convert to list and sort by title
        result = sorted(movies_by_title.values(), key=lambda x: x['title'])

        print(f"Normalized {len(result)} movies from Yelmo")
        return result


class ZentralcenterNormalizer(CinemaNormalizer):
    """Normalize Zentralcenter (Kinetike) cinema data"""

    @staticmethod
    def parse_date(date_str: str) -> str:
        """Convert DD/MM/YYYY to YYYY-MM-DD"""
        try:
            dt = datetime.strptime(date_str, '%d/%m/%Y')
            return dt.strftime('%Y-%m-%d')
        except ValueError:
            return date_str

    def normalize(self) -> List[Dict[str, Any]]:
        """
        Transform Zentralcenter data structure:
        - Group by movie title
        - Consolidate showings across multiple days
        - Convert dates to standard format
        """
        raw_data = self.load_data()

        # Group movies by title
        movies_by_title: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {
                'showings': {},
                'title': None,
                'length': None,
                'age': None,
                'theater': 'zentralcenter',
            }
        )

        for day_data in raw_data:
            date = self.parse_date(day_data['date'])
            day_name = day_data.get('day_name', '')

            for movie in day_data['movies']:
                title = movie['title']
                language = movie.get('language', 'SIN SUBTITULOS')

                # Use title + language as unique key
                movie_key = f"{title} - {language}"

                # Set movie metadata (only once)
                if not movies_by_title[movie_key]['title']:
                    movies_by_title[movie_key].update(
                        {
                            'title': title,
                            'length': movie.get('duration'),
                            'age': movie.get('age_rating'),
                            'language': language,
                        }
                    )

                # Add showings for this date
                showings_for_date = {}
                for sala, times in movie.get('showings', {}).items():
                    if times:  # Only add if there are actual times
                        showings_for_date[sala] = times

                if showings_for_date:
                    movies_by_title[movie_key]['showings'][date] = showings_for_date

        # Convert to list format and sort
        result = []
        for movie_key, movie_data in sorted(movies_by_title.items()):
            result.append(
                {
                    'title': movie_data['title'],
                    'length': movie_data['length'],
                    'age': movie_data['age'],
                    'theater': movie_data['theater'],
                    'language': movie_data.get('language'),
                    'showings': movie_data['showings'],
                    'actors': None,
                    'directors': None,
                    'genres': None,
                    'synopsis': None,
                    'url': None,
                }
            )

        print(f"✓ Normalized {len(result)} movies from Zentralcenter")
        return result


class XsurNormalizer(CinemaNormalizer):
    """Normalize X-Sur cinema data"""

    @staticmethod
    def parse_showings(showings_list: List[str]) -> Dict[str, List[str]]:
        """
        Parse X-Sur showings format from list of strings like:
        ["Lunes 09-02-2026 21:50", "Martes 10-02-2026 20:20 22:30"]

        Returns: {"2026-02-09": ["21:50"], "2026-02-10": ["20:20", "22:30"]}
        """
        result = defaultdict(list)

        for showing in showings_list:
            parts = showing.split()
            if len(parts) < 3:
                continue

            # Parse date (format: DD-MM-YYYY)
            try:
                date_str = parts[1]  # "09-02-2026"
                dt = datetime.strptime(date_str, '%d-%m-%Y')
                date = dt.strftime('%Y-%m-%d')

                # Parse times (rest of the parts)
                times = [t for t in parts[2:] if ':' in t]
                result[date].extend(times)
            except (ValueError, IndexError) as e:
                print(f"Warning: Could not parse showing '{showing}': {e}")
                continue

        return dict(result)

    @staticmethod
    def clean_text(text: str) -> str:
        """Fix encoding issues in X-Sur data"""
        replacements = {
            'Ã­': 'í',
            'Ã³': 'ó',
            'Ã±': 'ñ',
            'Ã©': 'é',
            'Ãº': 'ú',
            'Ã¡': 'á',
            'Ã"': 'Ó',
            'â€¦': '…',
        }
        for old, new in replacements.items():
            text = text.replace(old, new)
        return text

    def normalize(self) -> List[Dict[str, Any]]:
        """Transform X-Sur data to standard format"""
        raw_data = self.load_data()
        result = []

        for movie in raw_data:
            # Fix encoding issues
            title = self.clean_text(movie['title'])
            synopsis = self.clean_text(movie.get('synopsis', ''))
            age = self.clean_text(movie.get('age', ''))

            result.append(
                {
                    'title': title,
                    'length': movie.get('length'),
                    'age': age if age else None,
                    'theater': movie.get('theater', 'xsur'),
                    'showings': self.parse_showings(movie.get('showings', [])),
                    'actors': None,  # X-Sur doesn't provide this
                    'directors': None,
                    'genres': None,
                    'synopsis': synopsis if synopsis else None,
                    'url': None,
                }
            )

        print(f"✓ Normalized {len(result)} movies from X-Sur")
        return result


def normalize_all(input_dir: str = 'data_raw', output_dir: str = 'data') -> None:
    """
    Normalize all cinema data files

    Args:
        input_dir: Directory containing raw JSON files
        output_dir: Directory to save normalized JSON files
    """
    normalizers = {
        'yelmo': YelmoNormalizer,
        'zentralcenter': ZentralcenterNormalizer,
        'xsur': XsurNormalizer,
    }

    print("=" * 60)
    print("Cinema Data Normalization Pipeline")
    print("=" * 60)

    for cinema, normalizer_class in normalizers.items():
        input_file = f"{input_dir}/{cinema}.json"
        output_file = f"{output_dir}/{cinema}.json"

        print(f"\n📁 Processing {cinema}...")

        try:
            normalizer = normalizer_class(input_file, output_file)
            data = normalizer.normalize()
            normalizer.save_data(data)
        except FileNotFoundError:
            print(f"⚠️  File not found: {input_file}")
        except Exception as e:
            print(f"❌ Error processing {cinema}: {e}")
            import traceback

            traceback.print_exc()

    print("\n" + "=" * 60)
    print("✅ Normalization complete!")
    print("=" * 60)


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 2:
        normalize_all(sys.argv[1], sys.argv[2])
    elif len(sys.argv) > 1:
        normalize_all(sys.argv[1])
    else:
        normalize_all()
