from datetime import timedelta

from django.shortcuts import render
from django.utils import timezone

from movies.models import Movie


def home(request):
    # Get enriched movies only
    enriched_movies = Movie.objects.filter(
        tmdb_id__isnull=False,
        poster_path__isnull=False,
        release_date__isnull=False,
    ).exclude(poster_path="")

    # Last six movies added to the database
    last_added_movies = (
        Movie.objects.filter(
            tmdb_id__isnull=False,
            poster_path__isnull=False,
            release_date__isnull=False,
        )
        .exclude(poster_path="")
        .order_by("-created_at")[:6]
    )

    # Top picks of the month (recently added with high ratings)
    one_month_ago = timezone.now() - timedelta(days=30)
    top_month = enriched_movies.filter(created_at__gte=one_month_ago).order_by(
        "-vote_average"
    )[:6]

    # Top picks of the week
    one_week_ago = timezone.now() - timedelta(days=7)
    top_week = enriched_movies.filter(created_at__gte=one_week_ago).order_by(
        "-vote_average"
    )[:6]

    # Last movies added check
    if last_added_movies.count() > 0:
        last_added_movies = last_added_movies
    # If not enough recent movies, fall back to the highest ratetd
    if top_month.count() < 6:
        top_month = enriched_movies.order_by("-vote_average")[:6]
    if top_week.count() < 6:
        top_week = enriched_movies.order_by("-vote_average", "-created_at")[:6]

    return render(
        request,
        "whichmovie/home.html",
        {
            "top_month": top_month,
            "top_week": top_week,
            "last_added_movies": last_added_movies,
        },
    )


def privacy_policy(request):
    return render(request, "whichmovie/privacy_policy.html")


def terms_of_service(request):
    return render(request, "whichmovie/terms_of_service.html")
