from django.core.exceptions import ValidationError
from django.db import models


class Theater(models.Model):
    """Cinema theater with pricing information"""

    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    location = models.CharField(max_length=100)
    city = models.CharField(max_length=100)

    # Base pricing by day type
    # Store as JSON: {"weekday": 7.50, "weekend": 9.00, "holiday": 9.50}
    base_prices = models.JSONField(
        default=dict, blank=True, help_text="Base ticket prices by day type"
    )

    website = models.URLField(blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Movie(models.Model):
    """Movie with metadata - theater-agnostic"""

    title = models.CharField(max_length=200, db_index=True)
    slug = models.SlugField(max_length=200, unique=True)
    length = models.CharField(max_length=20, blank=True, null=True)
    age = models.CharField(max_length=3, blank=True, null=True)

    actors = models.JSONField(default=list, blank=True)
    directors = models.JSONField(default=list, blank=True)
    producers = models.JSONField(default=list, blank=True)
    genres = models.JSONField(default=list, blank=True)

    synopsis = models.TextField(blank=True, null=True, help_text="Primary synopsis to display")
    all_synopsis = models.JSONField(
        default=dict,
        blank=True,
    )

    all_urls = models.JSONField(
        default=dict,
        blank=True,
    )

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

    def get_synopsis(
        self, preferred_theaters: list = ['yelmo', 'multicines', 'xsur', 'zentralcenter']
    ) -> str:
        """
        Get best available synopsis

        Args:
            preferred_theaters: Priority order, e.g., ['yelmo', 'multicines', 'xsur']

        Returns:
            Best synopsis or empty string
        """
        if self.synopsis:
            return self.synopsis

        # Try preferred theaters in order
        for theater in preferred_theaters:
            if self.all_synopsis[theater]:
                return self.all_synopsis[theater]

        # Return any available synopsis
        for synopsis in self.all_synopsis.values():
            if synopsis:
                return synopsis

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

    # Format details
    format = models.CharField(max_length=50, blank=True, null=True)  # "2D ESPAÑOL", "3D", "VOSE"
    cinema = models.CharField(
        max_length=100, blank=True, null=True
    )  # Specific location within theater

    class Meta:
        ordering = ['date', 'time']
        indexes = [
            models.Index(fields=['movie', 'date']),
            models.Index(fields=['theater', 'date']),
            models.Index(fields=['date', 'time']),
        ]
        # Include all relevant fields in unique constraint
        unique_together = ['movie', 'theater', 'date', 'time', 'cinema', 'format']

    def __str__(self):
        return f"{self.movie.title} - {self.theater.name} - {self.date} {self.time}"

    @property
    def day_type(self) -> str:
        """
        Determine day type for pricing
        """
        # You can customize this logic
        weekday = self.date.weekday()

        # Monday-Thursday = weekday
        if weekday < 4:
            return 'weekday'
        # Friday-Sunday = weekend
        else:
            return 'weekend'

        # TODO: Add holiday detection
        # from django.utils import timezone
        # Check against a Holiday model or external calendar

    def clean(self):
        """Validate that showing is in the future (optional)"""
        from django.utils import timezone

        if self.date < timezone.now().date():
            raise ValidationError("Cannot create showings for past dates")
