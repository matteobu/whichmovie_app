from django.shortcuts import render

from .models import Movie


def movie_list(request):
    """Display list of all movies with TMDB enrichment data."""
    # Get only enriched movies (with release_date and poster)
    movies = (
        Movie.objects.filter(
            release_date__isnull=False,
            poster_path__isnull=False,
            overview__isnull=False,
        )
        .exclude(poster_path="")
        .exclude(overview="")
        .order_by("-release_date")
    )

    # Filter by year if provided
    year = request.GET.get("year")
    if year:
        movies = movies.filter(release_date__year=year)

    # Get available years for filter dropdown
    available_years = Movie.objects.filter(release_date__isnull=False).dates(
        "release_date", "year", order="DESC"
    )

    context = {
        "movies": movies,
        "total_movies": movies.count(),
        "enriched_movies": movies.filter(tmdb_id__isnull=False).count(),
        "available_years": [d.year for d in available_years],
        "selected_year": year,
    }

    return render(request, "movies/movie_list.html", context)
