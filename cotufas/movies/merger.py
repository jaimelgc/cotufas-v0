"""
Advanced Cinema Data Merger - Version 2
========================================

Improvements:
- Normalized format field
- Removed sala details (not needed for public display)
- Better duplicate merging
- Preserves all synopsis from different theaters
- Cleaner showing structure
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set


@dataclass
class Showing:
    """Structured showing data"""

    date: str
    time: str
    theater: str
    cinema: Optional[str] = None  # Specific location (e.g., "meridiano")
    format: Optional[str] = None  # Language/format (e.g., "2D ESPAÑOL", "VOSE")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict"""
        result = {
            'date': self.date,
            'time': self.time,
            'theater': self.theater,
        }
        if self.format:
            result['format'] = self.format
        return result

    def __hash__(self):
        """Make hashable for set operations"""
        return hash((self.date, self.time, self.theater, self.cinema, self.format))

    def __eq__(self, other):
        """Define equality for deduplication"""
        return (
            self.date == other.date
            and self.time == other.time
            and self.theater == other.theater
            and self.cinema == other.cinema
            and self.format == other.format
        )


@dataclass
class Movie:
    """Complete movie information"""

    title: str
    showings: List[Showing] = field(default_factory=list)
    length: Optional[str] = None
    age: Optional[str] = None
    actors: Optional[List[str]] = None
    directors: Optional[List[str]] = None
    genres: Optional[List[str]] = None
    synopsis: Optional[str] = None
    url: Optional[str] = None

    # Additional fields for merged movies
    theaters: Set[str] = field(default_factory=set)  # All theaters showing this
    all_synopsis: Dict[str, str] = field(default_factory=dict)  # Synopsis per theater
    all_urls: Dict[str, str] = field(default_factory=dict)  # URLs per theater

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict with full details"""
        return {
            'title': self.title,
            'length': self.length,
            'age': self.age,
            'theaters': sorted(list(self.theaters)),
            'showings': [
                s.to_dict() for s in sorted(self.showings, key=lambda x: (x.date, x.time))
            ],
            'actors': self.actors,
            'directors': self.directors,
            'genres': self.genres,
            'synopsis': self.synopsis,
            'all_synopsis': self.all_synopsis if len(self.all_synopsis) > 1 else None,
            'url': self.url,
            'all_urls': self.all_urls if len(self.all_urls) > 1 else None,
        }

    def add_showing(self, showing: Showing) -> None:
        """Add a showing with deduplication"""
        if showing not in self.showings:
            self.showings.append(showing)
            self.theaters.add(showing.theater)

    def merge_from(self, other: 'Movie') -> None:
        """Merge other movie's data into this one"""
        # Add all showings
        for showing in other.showings:
            self.add_showing(showing)

        # Merge synopsis
        if other.showings:
            if other.synopsis:
                self.all_synopsis[other.showings[0].theater] = other.synopsis
                if not self.synopsis:  # Use first non-empty synopsis as main
                    self.synopsis = other.synopsis

            # Merge URLs
            if other.url:
                self.all_urls[other.showings[0].theater] = other.url
                if not self.url:  # Use first non-empty URL as main
                    self.url = other.url

        # Prefer non-null metadata
        if not self.length and other.length:
            self.length = other.length
        if not self.actors and other.actors:
            self.actors = other.actors
        if not self.directors and other.directors:
            self.directors = other.directors
        if not self.genres and other.genres:
            self.genres = other.genres

    @property
    def total_showings(self) -> int:
        """Count total showings"""
        return len(self.showings)


class CinemaMerger:
    """Merge and analyze cinema data from multiple sources"""

    def __init__(self, data_dir: str = 'data'):
        self.data_dir = Path(data_dir)
        self.movies: List[Movie] = []

    def load_all(self) -> None:
        """Load all normalized JSON files"""
        for json_file in sorted(self.data_dir.glob('*.json')):
            theater_name = json_file.stem
            print(f"📂 Loading {theater_name}...")

            try:
                movies = self._load_theater_data(json_file, theater_name)
                self.movies.extend(movies)
                print(f"   Added {len(movies)} movies")
            except Exception as e:
                print(f"   ⚠️  Error: {e}")
                import traceback

                traceback.print_exc()

    def _load_theater_data(self, filepath: Path, theater: str) -> List[Movie]:
        """Load and parse data from a single theater"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        movies = []
        for item in data:
            movie = Movie(
                title=item['title'],
                length=item.get('length'),
                age=item.get('age'),
                actors=item.get('actors'),
                directors=item.get('directors'),
                genres=item.get('genres'),
                synopsis=item.get('synopsis'),
                url=item.get('url'),
            )

            # Parse showings based on structure
            showings_data = item.get('showings', {})

            for date, showing_list in showings_data.items():
                if isinstance(showing_list, list):
                    # New normalized format: [{"time": "18:00", "cinema": "...", "format": "..."}]
                    for showing_item in showing_list:
                        if isinstance(showing_item, dict):
                            # Dict format
                            theater_long = theater
                            if showing_item.get('cinema'):
                                theater_long = f"{theater}-{showing_item.get('cinema')}"
                            movie.add_showing(
                                Showing(
                                    date=date,
                                    time=showing_item['time'],
                                    theater=theater_long,
                                    cinema=showing_item.get('cinema'),
                                    format=showing_item.get('format') or item.get('format'),
                                )
                            )
                        else:
                            # Simple string format: ["18:00", "20:30"]
                            movie.add_showing(
                                Showing(
                                    date=date,
                                    time=showing_item,
                                    theater=theater,
                                    format=item.get('format'),
                                )
                            )
                elif isinstance(showing_list, dict):
                    # Old format: {"SALA 1": ["18:00", "20:00"]} - flatten it
                    for sala, times in showing_list.items():
                        for time in times:
                            movie.add_showing(
                                Showing(
                                    date=date,
                                    time=time,
                                    theater=theater,
                                    format=item.get('format'),
                                )
                            )

            movies.append(movie)

        return movies

    def normalize_title(self, title: str) -> str:
        """
        Normalize titles for matching across theaters
        Handles minor variations but not English vs Spanish
        """
        # Convert to lowercase and strip
        normalized = title.lower().strip()

        # Remove common punctuation variations
        normalized = normalized.replace(':', '').replace('-', ' ')

        # Normalize whitespace
        normalized = ' '.join(normalized.split())

        return normalized

    def get_unique_titles(self) -> Set[str]:
        """Get set of all unique movie titles"""
        return {movie.title for movie in self.movies}

    def merge_duplicates(self) -> List[Movie]:
        """
        Merge duplicate movies (same title) from different theaters
        Preserves all synopsis and URLs
        """
        merged: Dict[str, Movie] = {}

        for movie in self.movies:
            # Use normalized title for matching
            title_key = self.normalize_title(movie.title)

            if title_key not in merged:
                # First occurrence - create new entry
                merged[title_key] = Movie(
                    title=movie.title,  # Keep original casing
                    length=movie.length,
                    age=movie.age,
                    actors=movie.actors,
                    directors=movie.directors,
                    genres=movie.genres,
                    synopsis=movie.synopsis,
                    url=movie.url,
                )

                # Initialize collections
                if movie.synopsis:
                    merged[title_key].all_synopsis[
                        list(movie.theaters)[0] if movie.theaters else 'unknown'
                    ] = movie.synopsis
                if movie.url:
                    merged[title_key].all_urls[
                        list(movie.theaters)[0] if movie.theaters else 'unknown'
                    ] = movie.url

            # Merge this movie into the main entry
            merged[title_key].merge_from(movie)

        return sorted(merged.values(), key=lambda m: m.title)

    def export_merged(self, output_file: str = 'data/merged.json') -> None:
        """Export merged data"""
        merged = self.merge_duplicates()

        # Convert to dicts
        data = [movie.to_dict() for movie in merged]

        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"✓ Saved {len(data)} merged movies to {output_path}")

    def generate_statistics(self) -> Dict[str, Any]:
        """Generate statistics about the data"""
        unique_movies = self.merge_duplicates()

        stats = {
            'total_movie_entries': len(self.movies),
            'unique_movies': len(unique_movies),
            'theaters': {},
            'movies_by_age_rating': {},
        }

        # Theater statistics
        for movie in self.movies:
            for theater in movie.theaters:
                if theater not in stats['theaters']:
                    stats['theaters'][theater] = {
                        'movies': 0,
                        'showings': 0,
                    }

                stats['theaters'][theater]['movies'] += 1
                stats['theaters'][theater]['showings'] += movie.total_showings

        # Age rating distribution
        for movie in unique_movies:
            age = movie.age or 'Unknown'
            stats['movies_by_age_rating'][age] = stats['movies_by_age_rating'].get(age, 0) + 1

        return stats

    def print_statistics(self) -> None:
        """Print formatted statistics"""
        stats = self.generate_statistics()

        print("\n" + "=" * 60)
        print("📊 CINEMA DATA STATISTICS")
        print("=" * 60)
        print(f"\n📽️  Total Movie Entries: {stats['total_movie_entries']}")
        print(f"🎬 Unique Movies: {stats['unique_movies']}")

        print("\n🎭 By Theater:")
        for theater, data in sorted(stats['theaters'].items()):
            print(f"   {theater:20s} {data['movies']:3d} movies, {data['showings']:4d} showings")

        print("\n🔞 By Age Rating:")
        for age, count in sorted(
            stats['movies_by_age_rating'].items(), key=lambda x: (x[0] == 'Unknown', x[0])
        ):
            print(f"   {age:20s} {count:3d} movies")

        print("=" * 60 + "\n")


def main():
    """Main execution"""
    print("Cinema Data Merger V2")
    print("=" * 60)

    merger = CinemaMerger('data')
    merger.load_all()

    # Show statistics
    merger.print_statistics()

    # Export merged data
    merger.export_merged('data/merged.json')

    print("\n✅ Complete!")


if __name__ == '__main__':
    main()
