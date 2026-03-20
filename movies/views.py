from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_POST

from .models import Movie, Watchlist


@login_required
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

    watchlist_ids = list(
        Watchlist.objects.filter(user=request.user).values_list("movie_id", flat=True)
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
        "watchlist_ids": watchlist_ids,
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


@login_required
@require_POST
def toggle_watchlist(request):
    movie_id = request.POST.get("movie_id")
    movie = get_object_or_404(Movie, pk=movie_id)
    watchlist = Watchlist.objects.filter(user=request.user, movie=movie).first()
    if watchlist:
        watchlist.delete()
        added = False
    else:
        Watchlist.objects.create(user=request.user, movie=movie)
        added = True
    return JsonResponse({"added": added})


@login_required
def watchlist_page(request):
    """Display user's watchlist."""
    watchlist_items = (
        Watchlist.objects.filter(user=request.user)
        .select_related("movie")
        .order_by("-added_at")
    )
    movies = [item.movie for item in watchlist_items]

    context = {
        "movies": movies,
        "total_movies": len(movies),
    }

    return render(request, "movies/watchlist.html", context)
