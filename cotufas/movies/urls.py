from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import MovieViewSet, ShowingViewSet, TheaterViewSet

router = DefaultRouter()
router.register('theaters', TheaterViewSet)
router.register('movies', MovieViewSet)
router.register('showings', ShowingViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
