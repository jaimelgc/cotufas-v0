from django.test import TestCase

from .models import Movie, Showing, Theater


class TheaterFixtureText(TestCase):
    fixtures = ['merged.json']

    def test_theater_amount(self):
        self.assertEqual(Theater.objects.count(), 5)

    def test_theater_attributes(self):
        self.assertTrue(Theater.name.strip())
        self.assertTrue(Theater.slug.strip())
        self.assertTrue(Theater.location.strip())
        self.assertTrue(Theater.city.strip())
        self.assertTrue(Theater.base_prices)
        self.assertTrue(Theater.website)
