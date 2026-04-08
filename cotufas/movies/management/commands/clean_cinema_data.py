from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from ...models import Movie, Showing, Theater


class Command(BaseCommand):
    help = 'Filter data loaded into database'

    def filter_by_date(self):
        past_showings = Showing.objects.filter(date__lt=timezone.now().date())
        self.stdout.write(f'{len(past_showings)} showings deleted')
        past_showings.delete()

    def filter_by_showings(self):
        movies_without_showings = Movie.objects.filter(showings__isnull=True)
        self.stdout.write(f'{len(movies_without_showings)} movies deleted')
        movies_without_showings.delete()

    def filter_theater(self):
        null_theaters = Theater.objects.filter(city='')
        self.stdout.write(f'{len(null_theaters)} theaters deleted')
        null_theaters.delete()

    def handle(self, *args, **options):
        self.filter_by_date()
        self.filter_by_showings()
        self.filter_theater()