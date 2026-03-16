from django.core.exceptions import ValidationError
from django.db import models


class TheaterChain(models.Model):
    """Theater chain/brand (e.g., Yelmo, Multicines)"""

    name = models.CharField(max_length=50, unique=True)  # "yelmo", "xsur", etc.
    display_name = models.CharField(max_length=100)  # "Yelmo Cines"
    website = models.URLField(blank=True)

    def __str__(self):
        return self.display_name

    class Meta:
        ordering = ['display_name']


class Theater(models.Model):
    """Individual cinema location"""

    chain = models.ForeignKey(
        TheaterChain, on_delete=models.CASCADE, related_name='locations', null=True, blank=True
    )

    # Unique identifier: chain + location
    # Examples: "yelmo-meridiano", "yelmo-la-villa", "xsur", "multicines"
    slug = models.SlugField(max_length=100, unique=True)

    # Display name: "Yelmo Meridiano", "Yelmo La Villa de Orotava"
    name = models.CharField(max_length=100)

    # Location details
    city = models.CharField(max_length=100, blank=True)
    address = models.CharField(max_length=255, blank=True)

    # Pricing
    base_prices = models.JSONField(
        default=dict,
        blank=True,
        help_text="Base ticket prices by day type: {'weekday': 7.50, 'weekend': 9.00}",
    )

    format_surcharges = models.JSONField(
        default=dict, blank=True, help_text="Format surcharges: {'3D': 2.00, 'IMAX': 3.50}"
    )

    # Contact
    phone = models.CharField(max_length=20, blank=True)

    class Meta:
        ordering = ['chain', 'name']
        indexes = [
            models.Index(fields=['chain', 'slug']),
        ]

    def __str__(self):
        return self.name

    def get_price(self, day_type: str = 'weekday', format: str = None) -> float:
        """Calculate price for a showing"""
        base = self.base_prices.get(day_type, 0)

        if format:
            surcharge = 0
            for key, price in self.format_surcharges.items():
                if key.upper() in (format or '').upper():
                    surcharge = max(surcharge, price)
            return base + surcharge

        return base


class Movie(models.Model):
    """Movie with metadata - theater-agnostic"""

    title = models.CharField(max_length=200, db_index=True)
    length = models.CharField(max_length=20, blank=True, null=True)
    age = models.CharField(max_length=3, blank=True, null=True)

    actors = models.JSONField(default=list, blank=True)
    directors = models.JSONField(default=list, blank=True)
    producers = models.JSONField(default=list, blank=True)
    genres = models.JSONField(default=list, blank=True)

    synopsis = models.TextField(blank=True, null=True)
    all_synopsis = models.JSONField(default=dict, blank=True)

    url = models.URLField(blank=True, null=True)
    all_urls = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['title']
        indexes = [
            models.Index(fields=['title']),
            models.Index(fields=['age']),
        ]

    def __str__(self):
        return self.title

    def get_synopsis(self, preferred_chains: list = None) -> str:
        """Get best available synopsis"""
        if not preferred_chains:
            preferred_chains = ['yelmo', 'multicines', 'xsur', 'zentralcenter']

        if self.synopsis:
            return self.synopsis

        for chain in preferred_chains:
            if chain in self.all_synopsis and self.all_synopsis[chain]:
                return self.all_synopsis[chain]

        for synopsis in self.all_synopsis.values():
            if synopsis:
                return synopsis

        return ""

    def get_url(self, preferred_chains: list = None) -> str:
        """Get best available URL"""
        if not preferred_chains:
            preferred_chains = ['yelmo', 'multicines', 'xsur', 'zentralcenter']

        if self.url:
            return self.url

        for chain in preferred_chains:
            if chain in self.all_urls and self.all_urls[chain]:
                return self.all_urls[chain]

        for url in self.all_urls.values():
            if url:
                return url

        return ""

    @property
    def theaters_showing(self) -> list:
        """Get list of theaters showing this movie"""
        return list(self.showings.values_list('theater__name', flat=True).distinct())

    @property
    def age_display(self) -> str:
        """Human-readable age rating"""
        age_map = {
            '0': 'Todos los públicos',
            '7': 'Mayores de 7 años',
            '12': 'Mayores de 12 años',
            '16': 'Mayores de 16 años',
            '18': 'Mayores de 18 años',
        }
        return age_map.get(self.age, 'Clasificación desconocida')


class Showing(models.Model):
    """Individual showing of a movie at a theater"""

    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='showings')
    theater = models.ForeignKey(Theater, on_delete=models.CASCADE, related_name='showings')

    date = models.DateField(db_index=True)
    time = models.TimeField()

    format = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        ordering = ['date', 'time']
        indexes = [
            models.Index(fields=['movie', 'date']),
            models.Index(fields=['theater', 'date']),
            models.Index(fields=['date', 'time']),
        ]
        unique_together = ['movie', 'theater', 'date', 'time', 'format']

    def __str__(self):
        return f"{self.movie.title} - {self.theater.name} - {self.date} {self.time}"

    @property
    def day_type(self) -> str:
        """Determine day type for pricing"""
        weekday = self.date.weekday()
        if weekday < 4:
            return 'weekday'
        else:
            return 'weekend'

    @property
    def price(self) -> float:
        """Calculate price for this showing"""
        return self.theater.get_price(day_type=self.day_type, format=self.format)

    def clean(self):
        """Validate showing is in the future"""
        from django.utils import timezone

        if self.date < timezone.now().date():
            raise ValidationError("Cannot create showings for past dates")
