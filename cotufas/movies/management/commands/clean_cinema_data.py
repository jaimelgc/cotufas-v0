from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from ...models import Movie, Showing, Theater


class Command(BaseCommand):
    help = 'Filter data loaded into database'

    def filter_by_date(self):
        past_showings = Showing.objects.filter(date__lt=timezone.now().date())
        past_showings.delete()

    def filter_by_showings(self):
        movies_without_showings = Movie.objects.filter(showings__isnull=True)
        movies_without_showings.delete()
