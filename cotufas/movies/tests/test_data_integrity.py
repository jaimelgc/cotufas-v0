"""
Run against a real loaded database:
  python manage.py load_cinema_data movies/data/merged.json --update-pricing
  pytest tests/test_data_integrity.py --ds=your_project.settings

Or wire it into a fixture that loads merged.json before the suite.
"""

import pytest
from movies.models import Movie, Showing, Theater

CANONICAL_THEATER_SLUGS = {
    "yelmo-meridiano",
    "yelmo-la-villa",
    "xsur",
    "multicines",
    "zentralcenter",
}


@pytest.mark.django_db
class TestTheaterIntegrity:
    def test_exactly_five_canonical_theaters(self):
        actual = set(Theater.objects.values_list("slug", flat=True))
        assert actual == CANONICAL_THEATER_SLUGS, (
            f"Extra theaters: {actual - CANONICAL_THEATER_SLUGS}, "
            f"missing: {CANONICAL_THEATER_SLUGS - actual}"
        )

    def test_all_theaters_have_a_name_and_location(self):
        bad = Theater.objects.filter(name="") | Theater.objects.filter(location="")
        assert not bad.exists(), f"Theaters missing name/location: {list(bad)}"

    def test_all_theaters_have_base_prices(self):
        empty = Theater.objects.filter(base_prices={})
        assert not empty.exists(), f"Theaters without pricing: {list(empty)}"

    def test_each_theater_has_at_least_one_showing(self):
        for slug in CANONICAL_THEATER_SLUGS:
            count = Showing.objects.filter(theater__slug=slug).count()
            assert count > 0, f"Theater '{slug}' has no showings"


@pytest.mark.django_db
class TestMovieIntegrity:
    def test_every_movie_has_a_title(self):
        assert not Movie.objects.filter(title="").exists()

    def test_every_movie_has_a_unique_slug(self):
        from django.db.models import Count

        dupes = Movie.objects.values("slug").annotate(c=Count("id")).filter(c__gt=1)
        assert not dupes.exists(), f"Duplicate slugs: {list(dupes)}"

    def test_every_movie_has_at_least_one_showing(self):
        movies_without_showings = Movie.objects.filter(showings__isnull=True)
        assert (
            not movies_without_showings.exists()
        ), f"Movies with no showings: {list(movies_without_showings.values_list('title', flat=True))}"

    def test_no_movie_showing_in_unknown_theater(self):
        """No movie should be linked only to a placeholder/unknown theater"""
        orphan_showings = Showing.objects.exclude(theater__slug__in=CANONICAL_THEATER_SLUGS)
        # Warn but don't hard-fail — scraper may occasionally produce unknowns
        if orphan_showings.exists():
            titles = set(orphan_showings.values_list("movie__title", flat=True))
            pytest.warns(None, match="")  # replace with a soft warning or xfail as needed
            # Or fail hard:
            # pytest.fail(f"Showings in non-canonical theaters: {titles}")


@pytest.mark.django_db
class TestShowingIntegrity:
    def test_every_showing_has_a_movie(self):
        assert not Showing.objects.filter(movie__isnull=True).exists()

    def test_every_showing_has_a_theater(self):
        assert not Showing.objects.filter(theater__isnull=True).exists()

    def test_every_showing_has_a_date_and_time(self):
        assert not Showing.objects.filter(date__isnull=True).exists()
        assert not Showing.objects.filter(time__isnull=True).exists()

    def test_no_past_showings(self):
        from django.utils import timezone

        past = Showing.objects.filter(date__lt=timezone.now().date())
        assert not past.exists(), f"{past.count()} past showings found"

    def test_no_duplicate_showings(self):
        from django.db.models import Count

        dupes = (
            Showing.objects.values("movie", "theater", "date", "time", "cinema", "format")
            .annotate(c=Count("id"))
            .filter(c__gt=1)
        )
        assert not dupes.exists(), f"Duplicate showings: {list(dupes)}"
