"""
Cinema Data Normalization Pipeline - Version 2
===============================================

Improvements:
- Normalized age ratings to simple numbers
- Added URL extraction for all cinemas
- Standardized format field
- Removed sala (room) details for cleaner output
"""

import json
import re
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
        print(f"✓ Saved {len(data)} movies to {self.output_path}")

    @staticmethod
    def normalize_age(age_str: Optional[str]) -> str:
        """
        Normalize age ratings to simple number strings

        Examples:
            "M-18" -> "18"
            "No recomendada para menores de 12 años" -> "12"
            "Para todos los públicos" -> "0"
            None -> "0"
        """
        if not age_str:
            return "0"

        # Extract number from string
        match = re.search(r'\d+', age_str)
        if match:
            return match.group()

        # Check for "all ages" phrases
        all_ages_keywords = ['todos', 'all', 'general', 'apta', 'pdc', 'desc']
        if any(keyword in age_str.lower() for keyword in all_ages_keywords):
            return "0"

        # Default to 0 if can't determine
        return "0"

    def normalize(self) -> List[Dict[str, Any]]:
        """Override this method in subclasses"""
        raise NotImplementedError


class YelmoNormalizer(CinemaNormalizer):
    """Normalize Yelmo cinema data"""

    @staticmethod
    def convert_timestamp_to_date(timestamp: str) -> str:
        """Convert Yelmo's .NET timestamp to YYYY-MM-DD"""
        # .NET epoch is 0001-01-01, Unix epoch is 1970-01-01
        # Difference is 621355968000000000 ticks
        try:
            ticks = int(timestamp)
            unix_ticks = ticks - 621355968000000000
            unix_seconds = unix_ticks / 10000000
            dt = datetime.fromtimestamp(unix_seconds)
            return dt.strftime('%Y-%m-%d')
        except (ValueError, OSError):
            return timestamp

    def normalize(self) -> List[Dict[str, Any]]:
        """Transform Yelmo data"""
        raw_data = self.load_data()
        movies_by_title: Dict[str, Dict[str, Any]] = {}

        for item in raw_data:
            detail = item['detail']
            title = detail['title']

            if title not in movies_by_title:
                movies_by_title[title] = {
                    'title': title,
                    'length': detail.get('length'),
                    'age': self.normalize_age(detail.get('age')),
                    'theater': 'yelmo',
                    'showings': {},
                    'actors': detail.get('details', {}).get('Actores:'),
                    'directors': detail.get('details', {}).get('Directores:'),
                    'genres': [detail.get('genres')] if detail.get('genres') else None,
                    'synopsis': detail.get('synopsis'),
                    'url': detail.get('url'),
                }

            # Parse showings
            for cinema_name, formats in item['showings'].items():
                for format_name, dates in formats.items():
                    for timestamp, times in dates.items():
                        date = self.convert_timestamp_to_date(timestamp)

                        if date not in movies_by_title[title]['showings']:
                            movies_by_title[title]['showings'][date] = []

                        for time in times:
                            movies_by_title[title]['showings'][date].append(
                                {
                                    'time': time,
                                    'cinema': cinema_name,
                                    'format': format_name,
                                }
                            )

        result = sorted(movies_by_title.values(), key=lambda x: x['title'])
        print(f"✓ Normalized {len(result)} movies from Yelmo")
        return result


class ZentralcenterNormalizer(CinemaNormalizer):
    """Normalize Zentralcenter (Kinetike) cinema data"""

    BASE_URL = "https://kinetike.com:83/views/sesionesFuturas.aspx"

    @staticmethod
    def parse_date(date_str: str) -> str:
        """Convert DD/MM/YYYY to YYYY-MM-DD"""
        try:
            dt = datetime.strptime(date_str, '%d/%m/%Y')
            return dt.strftime('%Y-%m-%d')
        except ValueError:
            return date_str

    def normalize(self) -> List[Dict[str, Any]]:
        """Transform Zentralcenter data"""
        raw_data = self.load_data()
        movies_by_title: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {
                'showings': {},
                'title': None,
            }
        )

        for day_data in raw_data:
            date = self.parse_date(day_data['date'])

            for movie in day_data['movies']:
                title = movie['title']
                language = movie.get('language', 'SIN SUBTITULOS')

                # Use title + language as unique key
                movie_key = f"{title} - {language}"

                if not movies_by_title[movie_key]['title']:
                    movies_by_title[movie_key].update(
                        {
                            'title': title,
                            'length': movie.get('duration'),
                            'age': self.normalize_age(movie.get('age_rating')),
                            'theater': 'zentralcenter',
                            'format': language,
                            'actors': None,
                            'directors': None,
                            'genres': None,
                            'synopsis': None,
                            'url': movie.get('url'),
                        }
                    )

                # Add showings for this date (flatten sala structure)
                if date not in movies_by_title[movie_key]['showings']:
                    movies_by_title[movie_key]['showings'][date] = []

                for sala, times in movie.get('showings', {}).items():
                    for time in times:
                        movies_by_title[movie_key]['showings'][date].append(
                            {
                                'time': time,
                            }
                        )

        # Convert to list and clean up
        result = []
        for movie_data in sorted(movies_by_title.values(), key=lambda x: x['title']):
            result.append(
                {
                    'title': movie_data['title'],
                    'length': movie_data['length'],
                    'age': movie_data['age'],
                    'theater': movie_data['theater'],
                    'format': movie_data.get('format'),
                    'showings': movie_data['showings'],
                    'actors': movie_data['actors'],
                    'directors': movie_data['directors'],
                    'genres': movie_data['genres'],
                    'synopsis': movie_data['synopsis'],
                    'url': movie_data['url'],
                }
            )

        print(f"✓ Normalized {len(result)} movies from Zentralcenter")
        return result


class XsurNormalizer(CinemaNormalizer):
    """Normalize X-Sur cinema data"""

    BASE_URL = "https://x-surcine.com"

    @staticmethod
    def parse_showings(showings_list: List[str]) -> Dict[str, List[Dict[str, str]]]:
        """
        Parse X-Sur showings format
        Returns: {"2026-02-09": [{"time": "21:50"}], ...}
        """
        result = defaultdict(list)

        for showing in showings_list:
            parts = showing.split()
            if len(parts) < 3:
                continue

            try:
                date_str = parts[1]  # "09-02-2026"
                dt = datetime.strptime(date_str, '%d-%m-%Y')
                date = dt.strftime('%Y-%m-%d')

                # Parse times
                times = [t for t in parts[2:] if ':' in t]
                for time in times:
                    result[date].append({'time': time})
            except (ValueError, IndexError) as e:
                print(f"Warning: Could not parse showing '{showing}': {e}")
                continue

        return dict(result)

    @staticmethod
    def clean_text(text: str) -> str:
        """Fix encoding issues"""
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

    @staticmethod
    def extract_format(title: str) -> tuple[str, str]:
        """
        Extract format from title
        "MARTY SUPREME (ENGLISH VERSION)" -> ("MARTY SUPREME", "VOSE")
        "EVOLUTION" -> ("EVOLUTION", "Español")
        """
        if '(ENGLISH VERSION)' in title.upper():
            clean_title = re.sub(r'\s*\(ENGLISH VERSION\)\s*$', '', title, flags=re.IGNORECASE)
            return (clean_title.strip(), 'VOSE')
        return (title, 'Español')

    def normalize(self) -> List[Dict[str, Any]]:
        """Transform X-Sur data"""
        raw_data = self.load_data()
        result = []

        for movie in raw_data:
            # Fix encoding and extract format
            raw_title = self.clean_text(movie['title'])
            title, format_type = self.extract_format(raw_title)

            synopsis = self.clean_text(movie.get('synopsis', ''))
            age = self.clean_text(movie.get('age', ''))

            result.append(
                {
                    'title': title,
                    'length': movie.get('length'),
                    'age': self.normalize_age(age),
                    'theater': 'xsur',
                    'format': format_type,
                    'showings': self.parse_showings(movie.get('showings', [])),
                    'actors': None,  # X-Sur doesn't provide this
                    'directors': None,
                    'genres': None,
                    'synopsis': synopsis if synopsis else None,
                    'url': movie.get('url'),
                }
            )

        print(f"✓ Normalized {len(result)} movies from X-Sur")
        return result


class MulticinesNormalizer(CinemaNormalizer):
    """Normalize Multicines data (already mostly normalized)"""

    @staticmethod
    def parse_date(date_str: str) -> str:
        """Convert DD/MM/YYYY to YYYY-MM-DD"""
        try:
            dt = datetime.strptime(date_str, '%d/%m/%Y')
            return dt.strftime('%Y-%m-%d')
        except ValueError:
            return date_str

    def normalize(self) -> List[Dict[str, Any]]:
        """Transform Multicines data"""
        raw_data = self.load_data()
        result = []

        for movie in raw_data:
            # Parse showings into new format
            showings = {}
            for date_str, times in movie.get('showings', {}).items():
                date = self.parse_date(date_str)
                showings[date] = [{'time': time.strip()} for time in times]

            result.append(
                {
                    'title': movie['title'],
                    'length': movie.get('length'),
                    'age': self.normalize_age(movie.get('age')),
                    'theater': 'multicines',
                    'format': 'Español',  # Multicines doesn't specify
                    'showings': showings,
                    'actors': movie.get('actors'),
                    'directors': movie.get('directors'),
                    'genres': movie.get('genres'),
                    'synopsis': movie.get('synopsis'),
                    'url': movie.get('url'),
                }
            )

        print(f"✓ Normalized {len(result)} movies from Multicines")
        return result


def normalize_all(input_dir: str = 'data_raw', output_dir: str = 'data') -> None:
    """Normalize all cinema data files"""
    normalizers = {
        'yelmo': YelmoNormalizer,
        'zentralcenter': ZentralcenterNormalizer,
        'xsur': XsurNormalizer,
        'multicines': MulticinesNormalizer,
    }

    print("=" * 60)
    print("Cinema Data Normalization Pipeline V2")
    print("=" * 60)

    for cinema, normalizer_class in normalizers.items():
        input_file = f"{input_dir}/{cinema}_raw.json"
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
