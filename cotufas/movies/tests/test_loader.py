import json
from io import StringIO

import pytest
from django.core.management import call_command
from ..models import Movie, Showing, Theater

VALID_MOVIE = {
    "title": "Test Film",
    "length": "120 min",
    "age": "12",
    "theaters": ["xsur"],
    "actors": ["Actor One"],
    "directors": ["Director One"],
    "producers": [],  # intentionally empty — must be allowed
    "genres": ["Drama"],
    "synopsis": "A test film.",
    "all_synopsis": {},
    "all_urls": {},
    "showings": [
        {
            "theater": "xsur",
            "cinema": None,
            "date": "2099-01-15",
            "time": "18:00",
            "format": "2D ESPAÑOL",
        }
    ],
}


def call_loader(tmp_path, data, extra_args=None):
    f = tmp_path / "test.json"
    f.write_text(json.dumps(data))
    out = StringIO()
    args = [str(f)] + (extra_args or [])
    call_command("load_cinema_data", *args, stdout=out)
    return out.getvalue()


@pytest.mark.django_db
class TestLoaderHappyPath:
    def test_creates_movie_and_showing(self, tmp_path):
        call_loader(tmp_path, [VALID_MOVIE], ["--update-pricing"])
        assert Movie.objects.filter(title="Test Film").exists()
        assert Showing.objects.count() == 1

    def test_idempotent_on_rerun(self, tmp_path):
        call_loader(tmp_path, [VALID_MOVIE], ["--update-pricing"])
        call_loader(tmp_path, [VALID_MOVIE], ["--update-pricing"])
        assert Movie.objects.count() == 1
        assert Showing.objects.count() == 1

    def test_clear_flag_removes_movies_and_showings(self, tmp_path):
        call_loader(tmp_path, [VALID_MOVIE], ["--update-pricing"])
        call_loader(tmp_path, [VALID_MOVIE], ["--clear", "--update-pricing"])
        assert Movie.objects.count() == 1  # reloaded, not doubled
        assert Showing.objects.count() == 1

    def test_update_pricing_creates_exactly_five_theaters(self, tmp_path):
        call_loader(tmp_path, [], ["--update-pricing"])
        assert Theater.objects.count() == 5

    def test_five_theaters_have_correct_slugs(self, tmp_path):
        call_loader(tmp_path, [], ["--update-pricing"])
        expected = {"yelmo-meridiano", "yelmo-la-villa", "xsur", "multicines", "zentralcenter"}
        actual = set(Theater.objects.values_list("slug", flat=True))
        assert actual == expected

    def test_missing_producers_does_not_fail(self, tmp_path):
        movie = {**VALID_MOVIE, "producers": None}
        call_loader(tmp_path, [movie], ["--update-pricing"])
        m = Movie.objects.get(title="Test Film")
        assert m.producers == []

    def test_missing_synopsis_does_not_fail(self, tmp_path):
        movie = {**VALID_MOVIE, "synopsis": None, "all_synopsis": None}
        call_loader(tmp_path, [movie], ["--update-pricing"])
        m = Movie.objects.get(title="Test Film")
        assert m.get_synopsis() == ""


@pytest.mark.django_db
class TestLoaderEdgeCases:
    def test_past_showings_are_skipped(self, tmp_path):
        movie = {**VALID_MOVIE, "showings": [{**VALID_MOVIE["showings"][0], "date": "2000-01-01"}]}
        call_loader(tmp_path, [movie], ["--update-pricing"])
        assert Showing.objects.count() == 0
        assert Movie.objects.count() == 1  # movie still created

    def test_unknown_theater_creates_placeholder_not_crash(self, tmp_path):
        movie = {
            **VALID_MOVIE,
            "showings": [{**VALID_MOVIE["showings"][0], "theater": "ghost-cinema"}],
        }
        call_loader(tmp_path, [movie], ["--update-pricing"])
        # Showing still gets created against a minimal theater
        assert Showing.objects.count() == 1
        assert Theater.objects.filter(slug="ghost-cinema").exists()

    def test_unknown_theater_not_counted_in_five(self, tmp_path):
        movie = {
            **VALID_MOVIE,
            "showings": [{**VALID_MOVIE["showings"][0], "theater": "ghost-cinema"}],
        }
        call_loader(tmp_path, [movie], ["--update-pricing"])
        # The 5 canonical theaters + 1 ghost
        assert (
            Theater.objects.filter(
                slug__in=[
                    "yelmo-meridiano",
                    "yelmo-la-villa",
                    "xsur",
                    "multicines",
                    "zentralcenter",
                ]
            ).count()
            == 5
        )

    def test_duplicate_showings_not_doubled(self, tmp_path):
        showing = VALID_MOVIE["showings"][0]
        movie = {**VALID_MOVIE, "showings": [showing, showing]}
        call_loader(tmp_path, [movie], ["--update-pricing"])
        assert Showing.objects.count() == 1

    def test_yelmo_cinema_field_cleared_on_load(self, tmp_path):
        """Yelmo showings should store None as cinema, not the building name"""
        movie = {
            **VALID_MOVIE,
            "showings": [
                {
                    "theater": "yelmo-meridiano",
                    "cinema": "Sala 1",
                    "date": "2099-01-15",
                    "time": "18:00",
                    "format": "2D",
                }
            ],
        }
        call_loader(tmp_path, [movie], ["--update-pricing"])
        s = Showing.objects.first()
        assert s is not None
        assert s.cinema is None

    def test_bad_date_format_skips_showing_not_crash(self, tmp_path):
        movie = {**VALID_MOVIE, "showings": [{**VALID_MOVIE["showings"][0], "date": "not-a-date"}]}
        call_loader(tmp_path, [movie], ["--update-pricing"])
        assert Showing.objects.count() == 0

    def test_empty_json_array_does_not_crash(self, tmp_path):
        call_loader(tmp_path, [], ["--update-pricing"])
        assert Movie.objects.count() == 0
