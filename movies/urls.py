from django.urls import path

from . import views
from .views import movie_list

urlpatterns = [
    path("", movie_list, name="movie_list"),
    path("<int:pk>/", views.movie_detail, name="movie_detail"),
    path("watchlist/", views.watchlist_page, name="watchlist_page"),
    path("watchlist/toggle/", views.toggle_watchlist, name="toggle_watchlist"),
    path("feedback/", views.submit_feedback, name="submit_feedback"),
    path(
        "login-required/", views.login_required_message, name="login_required_message"
    ),
]
