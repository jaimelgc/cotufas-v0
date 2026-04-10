import pytest


@pytest.fixture(scope="session")
def loaded_db(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        yield
