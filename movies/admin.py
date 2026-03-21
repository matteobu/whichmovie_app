from urllib.parse import quote

from django.contrib import admin
from django.utils.html import format_html

from .models import Movie


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "source",
        "tmdb_id",
        "imdb_id",
        "youtube_link",
        "created_at",
    )
    list_filter = ("source", "created_at")
    search_fields = ("title", "original_title", "tmdb_id", "imdb_id")
    readonly_fields = ("created_at", "updated_at", "youtube_link", "tmdb_search_link")

    @admin.display(description="YouTube")
    def youtube_link(self, obj):
        if obj.video_id:
            return format_html(
                '<a href="https://www.youtube.com/watch?v={}" target="_blank">▶ Watch</a>',
                obj.video_id,
            )
        return "-"

    @admin.display(description="Search TMDB")
    def tmdb_search_link(self, obj):
        search_url = f"https://www.themoviedb.org/search?query={quote(obj.title)}"
        return format_html(
            '<a href="{}" target="_blank">🔍 Search on TMDB</a>', search_url
        )

    def save_model(self, request, obj, form, change):
        """When tmdb_id changes, re-fetch data from TMDB."""
        if change and "tmdb_id" in form.changed_data and obj.tmdb_id:
            from django.contrib import messages

            from contrib.tmdb import TMDBClient

            try:
                client = TMDBClient()
                tmdb_data = client.get_movie_details(obj.tmdb_id)

                if tmdb_data:
                    obj.overview = tmdb_data.get("overview")
                    obj.release_date = tmdb_data.get("release_date") or None
                    obj.poster_path = tmdb_data.get("poster_path")
                    obj.backdrop_path = tmdb_data.get("backdrop_path")
                    obj.genres = tmdb_data.get("genres")
                    obj.vote_average = tmdb_data.get("vote_average")
                    obj.vote_count = tmdb_data.get("vote_count")
                    obj.runtime = tmdb_data.get("runtime")
                    obj.popularity = tmdb_data.get("popularity")
                    obj.original_language = tmdb_data.get("original_language")
                    obj.production_countries = tmdb_data.get("production_countries")
                    messages.success(
                        request, f"Fetched TMDB data for: {tmdb_data.get('title')}"
                    )
                else:
                    messages.warning(
                        request, f"No data found for TMDB ID: {obj.tmdb_id}"
                    )
            except Exception as e:
                messages.error(request, f"Error fetching TMDB data: {e}")

        super().save_model(request, obj, form, change)
