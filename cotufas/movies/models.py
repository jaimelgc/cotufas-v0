from django.db import models


class Theater(models.Model):
    name = models.CharField(max_length=50, unique=True)
    location = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class Movie(models.Model):
    title = models.CharField(max_length=200)
    length = models.CharField(max_length=20, blank=True, null=True)
    age = models.CharField(max_length=20, blank=True, null=True)

    theater = models.ForeignKey(Theater, on_delete=models.CASCADE, related_name='movies')
    format = models.CharField(max_length=50, blank=True, null=True)
    actors = models.JSONField(default=list, blank=True)
    directors = models.JSONField(default=list, blank=True)
    producers = models.JSONField(default=list, blank=True)
    genres = models.JSONField(default=list, blank=True)

    synopsis = models.TextField(blank=True, null=True)
    url = models.URLField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['title']
        indexes = [
            models.Index(fields=['theater', 'title']),
        ]

    def __str__(self):
        return f"{self.title} ({self.theater.name})"


class Showing(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='showings')
    date = models.DateField()
    time = models.TimeField()
    price = models.IntegerField(blank=True, null=True)

    class Meta:
        ordering = ['date', 'time']
        indexes = [
            models.Index(fields=['movie', 'date']),
        ]
        unique_together = ['movie', 'date', 'time']

    def __str__(self):
        return f"{self.movie.title} - {self.date} {self.time}"
