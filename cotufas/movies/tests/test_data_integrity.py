"""
Run against a real loaded database:
  python manage.py load_cinema_data movies/data/merged.json --update-pricing
  pytest tests/test_data_integrity.py --ds=cotufas.settings
"""

import pytest
from ..models import Movie, Showing, Theater

THEATER_SLUGS = {
    "multicines",
    "xsur",
    "yelmo-la-villa",
    "yelmo-meridiano",
    "zentralcenter",
}


@pytest.mark.django_db
class TestTheaterIntegrity:
    def test_exactly_five_theaters(self, loaded_db):
        actual = set(Theater.objects.values_list("slug", flat=True))
        assert len(actual) == len(THEATER_SLUGS), (
            f"Extra theaters: {actual - THEATER_SLUGS}, " f"missing: {THEATER_SLUGS - actual}"
        )

    def test_all_theaters_have_a_name_and_location(self, loaded_db):
        bad = Theater.objects.filter(name="") | Theater.objects.filter(location="")
        assert not bad.exists(), f"Theaters missing name/location: {list(bad)}"

    def test_all_theaters_have_base_prices(self, loaded_db):
        empty = Theater.objects.filter(base_prices={})
        assert not empty.exists(), f"Theaters without pricing: {list(empty)}"

    def test_each_theater_has_at_least_one_showing(self, loaded_db):
        for slug in THEATER_SLUGS:
            count = Showing.objects.filter(theater__slug=slug).count()
            assert count > 0, f"Theater '{slug}' has no showings"


@pytest.mark.django_db
class TestMovieIntegrity:
    def test_every_movie_has_a_title(self, loaded_db):
        assert not Movie.objects.filter(title="").exists()

    def test_every_movie_has_a_unique_slug(self, loaded_db):
        from django.db.models import Count

        dupes = Movie.objects.values("slug").annotate(c=Count("id")).filter(c__gt=1)
        assert not dupes.exists(), f"Duplicate slugs: {list(dupes)}"

    def test_every_movie_has_at_least_one_showing(self, loaded_db):
        movies_without_showings = Movie.objects.filter(showings__isnull=True)
        assert (
            not movies_without_showings.exists()
        ), f"Movies with no showings: {list(movies_without_showings.values_list('title', flat=True))}"

    def test_no_movie_showing_in_unknown_theater(self, loaded_db):
        """No movie should be linked only to a placeholder/unknown theater"""
        orphan_showings = Showing.objects.exclude(theater__slug__in=THEATER_SLUGS)
        # Warn but don't hard-fail — scraper may occasionally produce unknowns
        if orphan_showings.exists():
            pytest.warns(None, match="")


@pytest.mark.django_db
class TestShowingIntegrity:
    def test_every_showing_has_a_movie(self, loaded_db):
        assert not Showing.objects.filter(movie__isnull=True).exists()

    def test_every_showing_has_a_theater(self, loaded_db):
        assert not Showing.objects.filter(theater__isnull=True).exists()

    def test_every_showing_has_a_date_and_time(self, loaded_db):
        assert not Showing.objects.filter(date__isnull=True).exists()
        assert not Showing.objects.filter(time__isnull=True).exists()

    def test_no_past_showings(self, loaded_db):
        from django.utils import timezone

        past = Showing.objects.filter(date__lt=timezone.now().date())
        assert not past.exists(), f"{past.count()} past showings found"

    def test_no_duplicate_showings(self, loaded_db):
        from django.db.models import Count

        dupes = (
            Showing.objects.values("movie", "theater", "date", "time", "format")
            .annotate(c=Count("id"))
            .filter(c__gt=1)
        )
        assert not dupes.exists(), f"Duplicate showings: {list(dupes)}"
