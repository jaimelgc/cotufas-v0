from rest_framework import serializers

from .models import Movie, Showing, Theater


class TheaterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Theater
        fields = '__all__'


class MovieSerializer(serializers.ModelSerializer):
    class Meta:
        model = Movie
        fields = '__all__'


class ShowingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Showing
        fields = '__all__'
