from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMessage
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .models import Movie, Watchlist


def login_required_message(request):
    """Show a message that watchlist requires login and redirect back."""
    messages.info(
        request, "Watchlist is available for logged in users. Please login or sign up."
    )
    return redirect("movie_list")


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

    # Only get watchlist for authenticated users
    if request.user.is_authenticated:
        watchlist_ids = list(
            Watchlist.objects.filter(user=request.user).values_list(
                "movie_id", flat=True
            )
        )
    else:
        watchlist_ids = []

    # Search by title
    search_query = request.GET.get("q", "").strip()
    if search_query:
        movies = movies.filter(title__icontains=search_query)

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
        "search_query": search_query,
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


@require_POST
def submit_feedback(request):
    """Handle movie feedback submission and send email."""
    import logging

    logger = logging.getLogger(__name__)

    movie_id = request.POST.get("movie_id")
    movie_title = request.POST.get("movie_title")
    message = request.POST.get("message")

    if not message:
        return JsonResponse({"success": False, "error": "Message is required"})

    # Build email content
    subject = f"Movie Feedback: {movie_title}"
    body = f"""
Movie Feedback Report
=====================

Movie: {movie_title}
Movie ID: {movie_id}

User Feedback:
{message}

---
Sent from WhichMovie
"""

    recipient = getattr(settings, "DEFAULT_REPLY_TO_EMAIL", settings.DEFAULT_FROM_EMAIL)

    try:
        email = EmailMessage(
            subject=subject,
            body=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[recipient],
            reply_to=[recipient],
        )
        email.send()
        logger.info(f"Feedback email sent for movie: {movie_title}")
        return JsonResponse({"success": True})
    except Exception as e:
        logger.error(f"Failed to send feedback email: {e}")
        print(f"Email error: {e}")  # This will show in console
        return JsonResponse({"success": False, "error": str(e)})
