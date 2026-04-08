import pytest
from django.core.management import call_command


@pytest.fixture(scope="session")
def loaded_db(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        call_command(
            "load_cinema_data",
            "movies/data/merged.json",
            "--update-pricing",
            "--clear",
        )
