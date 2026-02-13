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

    # Filter by genre if provided
    genre = request.GET.get("genre")
    if genre:
        movies = movies.filter(genres__contains=[genre])

    # Filter by minimum rating if provided
    rating = request.GET.get("rating")
    if rating:
        movies = movies.filter(vote_average__gte=float(rating))

    # Get available years for filter dropdown
    available_years = Movie.objects.filter(release_date__isnull=False).dates(
        "release_date", "year", order="DESC"
    )

    # Get available genres for filter dropdown
    all_genres = set()
    for g in Movie.objects.filter(genres__isnull=False).values_list(
        "genres", flat=True
    ):
        if g:
            all_genres.update(g)
    available_genres = sorted(all_genres)

    # Rating options
    rating_options = [
        ("9", "9+ Excellent"),
        ("8", "8+ Great"),
        ("7", "7+ Good"),
        ("6", "6+ Above Average"),
        ("5", "5+ Average"),
    ]

    context = {
        "movies": movies,
        "total_movies": movies.count(),
        "enriched_movies": movies.filter(tmdb_id__isnull=False).count(),
        "available_years": [d.year for d in available_years],
        "available_genres": available_genres,
        "rating_options": rating_options,
        "selected_year": year,
        "selected_genre": genre,
        "selected_rating": rating,
    }

    return render(request, "movies/movie_list.html", context)
