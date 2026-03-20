from django.conf import settings
from django.db import models


class Movie(models.Model):
    """
    Movie model to store movie data from multiple sources (YouTube, TMDB, Festivals).

    The model stores the title/original_title from the source, and external IDs
    (tmdb_id, imdb_id) for deduplication and future enrichment with TMDB data.
    """

    # Core identifiers
    title = models.CharField(max_length=255)
    original_title = models.CharField(max_length=255, blank=True, null=True)

    # External IDs for deduplication and enrichment
    tmdb_id = models.IntegerField(blank=True, null=True, unique=True)
    imdb_id = models.CharField(max_length=20, blank=True, null=True, unique=True)

    # Source tracking
    source = models.CharField(
        max_length=50,
        help_text="Source of the title (e.g., 'youtube_title', 'festival_title')",
    )
    video_id = models.CharField(
        max_length=50, blank=True, null=True
    )  # YouTube video ID

    # TMDB enrichment fields (populated by enrich_movies_with_tmdb task)
    overview = models.TextField(blank=True, null=True)
    release_date = models.DateField(blank=True, null=True)
    poster_path = models.CharField(max_length=255, blank=True, null=True)
    backdrop_path = models.CharField(max_length=255, blank=True, null=True)

    # Additional TMDB fields
    genres = models.JSONField(blank=True, null=True)  # List of genre names
    vote_average = models.FloatField(blank=True, null=True)
    vote_count = models.IntegerField(blank=True, null=True)
    runtime = models.IntegerField(blank=True, null=True)  # Minutes
    popularity = models.FloatField(blank=True, null=True)
    original_language = models.CharField(max_length=10, blank=True, null=True)
    production_countries = models.JSONField(
        blank=True, null=True
    )  # List of country codes

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ["-created_at"]


class Watchlist(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.movie.title}"

    class Meta:
        ordering = ["-added_at"]
        unique_together = ("user", "movie")
