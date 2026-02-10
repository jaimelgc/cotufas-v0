from django.db import models


class Movie(models.Model):
    title = models.CharField(max_length=100)
    synopsis = models.TextField()
    age = models.IntegerField()
    showings = {}
    genres = []
    directors = []
    actors = []
