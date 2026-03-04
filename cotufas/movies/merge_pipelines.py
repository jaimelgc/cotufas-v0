"""
Advanced Cinema Data Merger
============================

Demonstrates additional professional Python techniques:
- DataClasses for structured data
- Generators for memory efficiency
- Set operations for deduplication
- Operator module for sorting
- Iterator tools
"""

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from itertools import groupby
from operator import itemgetter
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Set


@dataclass
class Showing:
    """Structured showing data"""

    date: str
    time: str
    theater: str
    cinema: Optional[str] = None
    format: Optional[str] = None
    url: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict"""
        return {
            'date': self.date,
            'time': self.time,
            'theater': self.theater,
            'cinema': self.cinema,
            'format': self.format,
            'url': self.url,
        }

    def __hash__(self):
        """Make hashable for set operations"""
        return hash((self.date, self.time, self.theater))

    def __eq__(self, other):
        """Define equality for deduplication"""
        return self.date == other.date and self.time == other.time and self.theater == other.theater


@dataclass
class Movie:
    """Complete movie information"""

    title: str
    theater: str
    showings: List[Showing] = field(default_factory=list)
    length: Optional[str] = None
    age: Optional[str] = None
    actors: Optional[List[str]] = None
    directors: Optional[List[str]] = None
    genres: Optional[List[str]] = None
    synopsis: Optional[str] = None
    url: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict"""
        return {
            'title': self.title,
            'length': self.length,
            'age': self.age,
            'theater': self.theater,
            'showings': [s.to_dict() for s in self.showings],
            'actors': self.actors,
            'directors': self.directors,
            'genres': self.genres,
            'synopsis': self.synopsis,
            'url': self.url,
        }

    def group_showings_by_date(self) -> Dict[str, List[str]]:
        """Group showings by date for cleaner output"""
        grouped = {}
        # Sort by date, then group
        sorted_showings = sorted(self.showings, key=lambda s: (s.date, s.time))

        for date, group in groupby(sorted_showings, key=lambda s: s.date):
            times = [showing.time for showing in group]
            grouped[date] = sorted(set(times))  # Deduplicate times

        return grouped

    def add_showing(self, showing: Showing) -> None:
        """Add a showing (with deduplication)"""
        if showing not in self.showings:
            self.showings.append(showing)

    @property
    def total_showings(self) -> int:
        """Count total showings"""
        return len(self.showings)

    @property
    def date_range(self) -> tuple[str, str]:
        """Get first and last showing dates"""
        if not self.showings:
            return ("", "")
        dates = sorted(set(s.date for s in self.showings))
        return (dates[0], dates[-1])


class CinemaMerger:
    """Merge and analyze cinema data from multiple sources"""

    def __init__(self, data_dir: str = 'data'):
        self.data_dir = Path(data_dir)
        self.movies: List[Movie] = []

    def load_all(self) -> None:
        """Load all normalized JSON files"""
        for json_file in self.data_dir.glob('*.json'):
            theater_name = json_file.stem  # filename without .json
            print(f"📂 Loading {theater_name}...")

            try:
                movies = self._load_theater_data(json_file, theater_name)
                self.movies.extend(movies)
                print(f"   Added {len(movies)} movies")
            except Exception as e:
                print(f"   ⚠️  Error: {e}")

    def _load_theater_data(self, filepath: Path, theater: str) -> List[Movie]:
        """Load and parse data from a single theater"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        movies = []
        for item in data:
            movie = Movie(
                title=item['title'],
                theater=theater,
                length=item.get('length'),
                age=item.get('age'),
                actors=item.get('actors'),
                directors=item.get('directors'),
                genres=item.get('genres'),
                synopsis=item.get('synopsis'),
                url=item.get('url'),
            )

            # Parse showings
            for date, times in item.get('showings', {}).items():
                # Handle both formats: dict of times or list of times
                if isinstance(times, dict):
                    # Format: {"SALA 1": ["18:00", "20:00"]}
                    for sala, time_list in times.items():
                        for time in time_list:
                            movie.add_showing(Showing(date=date, time=time, theater=theater))
                elif isinstance(times, list):
                    # Format: ["18:00", "20:00"]
                    for time in times:
                        movie.add_showing(Showing(date=date, time=time, theater=theater))

            movies.append(movie)

        return movies

    def get_unique_titles(self) -> Set[str]:
        """Get set of all unique movie titles"""
        return {movie.title for movie in self.movies}

    def get_movies_by_title(self, title: str) -> List[Movie]:
        """Get all instances of a movie across theaters"""
        return [m for m in self.movies if m.title == title]

    def get_movies_by_theater(self, theater: str) -> List[Movie]:
        """Filter movies by theater"""
        return [m for m in self.movies if m.theater == theater]

    def merge_duplicates(self) -> List[Movie]:
        """
        Merge duplicate movies (same title) from different theaters
        into single entries
        """
        merged: Dict[str, Movie] = {}

        for movie in self.movies:
            if movie.title not in merged:
                # First occurrence - create new entry
                merged[movie.title] = Movie(
                    title=movie.title,
                    theater=f"multiple ({movie.theater})",
                    length=movie.length,
                    age=movie.age,
                    actors=movie.actors,
                    directors=movie.directors,
                    genres=movie.genres,
                    synopsis=movie.synopsis,
                    url=movie.url,
                )

            # Add all showings
            for showing in movie.showings:
                merged[movie.title].add_showing(showing)

            # Update theater list
            current_theaters = merged[movie.title].theater
            if movie.theater not in current_theaters:
                if current_theaters.startswith("multiple"):
                    merged[movie.title].theater = f"{current_theaters}, {movie.theater}"

        return list(merged.values())

    def export_merged(self, output_file: str = 'data/merged.json') -> None:
        """Export merged data"""
        merged = self.merge_duplicates()

        # Sort by title
        merged.sort(key=lambda m: m.title)

        # Convert to dicts
        data = [movie.to_dict() for movie in merged]

        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"✓ Saved {len(data)} merged movies to {output_path}")

    def generate_statistics(self) -> Dict[str, Any]:
        """Generate statistics about the data"""
        stats = {
            'total_movies': len(self.movies),
            'unique_titles': len(self.get_unique_titles()),
            'theaters': {},
            'movies_by_age_rating': {},
            'date_range': self._get_overall_date_range(),
        }

        # Theater statistics
        for movie in self.movies:
            theater = movie.theater
            if theater not in stats['theaters']:
                stats['theaters'][theater] = {
                    'movies': 0,
                    'showings': 0,
                }

            stats['theaters'][theater]['movies'] += 1
            stats['theaters'][theater]['showings'] += movie.total_showings

        # Age rating distribution
        for movie in self.movies:
            age = movie.age or 'Unknown'
            stats['movies_by_age_rating'][age] = stats['movies_by_age_rating'].get(age, 0) + 1

        return stats

    def _get_overall_date_range(self) -> tuple[str, str]:
        """Get the overall date range of all showings"""
        all_dates = []
        for movie in self.movies:
            all_dates.extend(s.date for s in movie.showings)

        if not all_dates:
            return ("", "")

        all_dates = sorted(set(all_dates))
        return (all_dates[0], all_dates[-1])

    def print_statistics(self) -> None:
        """Print formatted statistics"""
        stats = self.generate_statistics()

        print("\n" + "=" * 60)
        print("📊 CINEMA DATA STATISTICS")
        print("=" * 60)
        print(f"\n📽️  Total Movies: {stats['total_movies']}")
        print(f"🎬 Unique Titles: {stats['unique_titles']}")
        print(f"📅 Date Range: {stats['date_range'][0]} → {stats['date_range'][1]}")

        print(f"\n🎭 By Theater:")
        for theater, data in sorted(stats['theaters'].items()):
            print(f"   {theater:20s} {data['movies']:3d} movies, {data['showings']:4d} showings")

        print(f"\n🔞 By Age Rating:")
        for age, count in sorted(stats['movies_by_age_rating'].items()):
            print(f"   {age:20s} {count:3d} movies")

        print("=" * 60 + "\n")


def main():
    """Main execution"""
    print("Cinema Data Merger")
    print("=" * 60)

    merger = CinemaMerger('data')
    merger.load_all()

    # Show statistics
    merger.print_statistics()

    # Export merged data
    merger.export_merged('data/merged.json')

    # Also export by theater
    print("\n📁 Exporting by theater...")
    for theater in ['yelmo', 'xsur', 'zentralcenter']:
        try:
            theater_movies = merger.get_movies_by_theater(theater)
            data = [m.to_dict() for m in sorted(theater_movies, key=lambda x: x.title)]

            output = Path(f'data/by_theater/{theater}.json')
            output.parent.mkdir(parents=True, exist_ok=True)

            with open(output, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            print(f"   ✓ {theater}: {len(data)} movies")
        except Exception as e:
            print(f"   ⚠️  {theater}: {e}")

    print("\n✅ Complete!")


if __name__ == '__main__':
    main()
