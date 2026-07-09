from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, permissions, viewsets
from drf_spectacular.utils import extend_schema

from .models import Movie, Showing, Theater
from .serializers import MovieSerializer, ShowingSerializer, TheaterSerializer

@extend_schema(
    summary="Theater Endpoint Set",
    description="A full CRUD viewset related to theaters.",
    responses={200: None},
)
class TheaterViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Theater.objects.all()
    serializer_class = TheaterSerializer
    permission_classes = [permissions.AllowAny]

    filter_backends = [filters.SearchFilter]
    search_fields = ['slug']


@extend_schema(
    summary="Movie Endpoint Set",
    description="A full CRUD viewset related to movies.",
    responses={200: None},
)
class MovieViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Movie.objects.all()
    serializer_class = MovieSerializer
    permission_classes = [permissions.AllowAny]

    filter_backends = [filters.SearchFilter]
    search_fields = ['slug']


@extend_schema(
    summary="Showing Endpoint Set",
    description="A full CRUD viewset related to showings.",
    responses={200: None},
)
class ShowingViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Showing.objects.all()
    serializer_class = ShowingSerializer
    permission_classes = [permissions.AllowAny]

    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["movie", "theater"]
    search_fields = ["movie__slug", "theater__slug"]
