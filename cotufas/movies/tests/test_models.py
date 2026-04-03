import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone
from movies.models import Movie, Showing, Theater


@pytest.fixture
def theater(db):
    return Theater.objects.create(
        name="xsur", slug="xsur",
        location="C. Lisboa", city="Costa Adeje"
    )


@pytest.fixture
def movie(db):
    return Movie.objects.create(title="Test Movie", slug="test-movie")


@pytest.fixture
def showing(db, movie, theater):
    return Showing.objects.create(
        movie=movie, theater=theater,
        date=timezone.now().date() + timezone.timedelta(days=1),
        time="18:00"
    )


class TestTheater:
    def test_name_must_be_unique(self, db, theater):
        with pytest.raises(Exception):  # IntegrityError
            Theater.objects.create(name="xsur", slug="xsur-2", location="x", city="y")

    def test_slug_must_be_unique(self, db, theater):
        with pytest.raises(Exception):
            Theater.objects.create(name="xsur 2", slug="xsur", location="x", city="y")

    def test_base_prices_defaults_to_empty_dict(self, db):
        t = Theater.objects.create(name="empty", slug="empty", location="x", city="y")
        assert t.base_prices == {}

    def test_str(self, theater):
        assert str(theater) == "xsur"


class TestMovie:
    def test_json_fields_default_to_empty(self, db):
        m = Movie.objects.create(title="No Data", slug="no-data")
        assert m.actors == []
        assert m.directors == []
        assert m.producers == []  # producers can be missing — this must not raise
        assert m.genres == []
        assert m.all_synopsis == {}

    def test_get_synopsis_falls_back_through_preferences(self, db):
        m = Movie.objects.create(
            title="S", slug="s",
            all_synopsis={"yelmo": "Yelmo synopsis", "xsur": "Xsur synopsis"}
        )
        # No primary synopsis set — should pick from preferred order
        assert m.get_synopsis(preferred_theaters=["yelmo"]) == "Yelmo synopsis"

    def test_get_synopsis_returns_empty_string_when_none(self, db):
        m = Movie.objects.create(title="Empty", slug="empty-s")
        assert m.get_synopsis() == ""

    def test_get_synopsis_prefers_primary_over_all(self, db):
        m = Movie.objects.create(
            title="Primary", slug="primary-s",
            synopsis="Primary synopsis",
            all_synopsis={"yelmo": "Yelmo synopsis"}
        )
        assert m.get_synopsis() == "Primary synopsis"

    def test_age_display_known_ratings(self, db):
        for age, expected in [("0", "Todos los públicos"), ("18", "Mayores de 18 años")]:
            m = Movie.objects.create(title=f"Movie {age}", slug=f"movie-{age}", age=age)
            assert m.age_display == expected

    def test_age_display_unknown_rating(self, db):
        m = Movie.objects.create(title="Unknown Age", slug="unknown-age", age="99")
        assert m.age_display == "Clasificación desconocida"

    def test_slug_must_be_unique(self, db):
        Movie.objects.create(title="Dupe", slug="dupe")
        with pytest.raises(Exception):
            Movie.objects.create(title="Dupe 2", slug="dupe")


class TestShowing:
    def test_requires_movie_and_theater(self, db):
        with pytest.raises(Exception):
            Showing.objects.create(date="2099-01-01", time="18:00")

    def test_unique_together_prevents_duplicates(self, db, movie, theater):
        future = timezone.now().date() + timezone.timedelta(days=1)
        Showing.objects.create(movie=movie, theater=theater, date=future, time="18:00")
        with pytest.raises(Exception):
            Showing.objects.create(movie=movie, theater=theater, date=future, time="18:00")

    def test_different_format_same_slot_is_allowed(self, db, movie, theater):
        future = timezone.now().date() + timezone.timedelta(days=1)
        Showing.objects.create(movie=movie, theater=theater, date=future, time="18:00", format="2D")
        # Should not raise — format is part of unique_together
        Showing.objects.create(movie=movie, theater=theater, date=future, time="18:00", format="3D")

    def test_day_type_weekday(self, db, movie, theater):
        # Find a Monday
        from datetime import date
        d = date(2025, 4, 7)  # Known Monday
        s = Showing.objects.create(movie=movie, theater=theater, date=d, time="18:00")
        assert s.day_type == "weekday"

    def test_day_type_weekend(self, db, movie, theater):
        from datetime import date
        d = date(2025, 4, 12)  # Known Saturday
        s = Showing.objects.create(movie=movie, theater=theater, date=d, time="18:00")
        assert s.day_type == "weekend"

    def test_clean_rejects_past_dates(self, db, movie, theater):
        yesterday = timezone.now().date() - timezone.timedelta(days=1)
        s = Showing(movie=movie, theater=theater, date=yesterday, time="18:00")
        with pytest.raises(ValidationError):
            s.clean()
