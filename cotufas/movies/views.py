from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, permissions, viewsets

from .models import Movie, Showing, Theater
from .serializers import MovieSerializer, ShowingSerializer, TheaterSerializer


class TheaterViewSet(viewsets.ModelViewSet):
    queryset = Theater.objects.all()
    serializer_class = TheaterSerializer
    permission_classes = [permissions.AllowAny]

    filter_backends = [filters.SearchFilter]
    search_fields = ['slug']


class MovieViewSet(viewsets.ModelViewSet):
    queryset = Movie.objects.all()
    serializer_class = MovieSerializer
    permission_classes = [permissions.AllowAny]

    filter_backends = [filters.SearchFilter]
    search_fields = ['slug']


class ShowingViewSet(viewsets.ModelViewSet):
    queryset = Showing.objects.all()
    serializer_class = ShowingSerializer
    permission_classes = [permissions.AllowAny]

    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_backends = ['movie', 'theater', 'update']
    search_fields = ['movie__slug', 'theater__slug']
