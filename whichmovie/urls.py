from django.contrib import admin
from django.urls import include, path

from accounts.views import signup_view

from . import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.home, name="home"),  # landing page
    path("movies/", include("movies.urls")),  # movies page
    path("accounts/", include("django.contrib.auth.urls")),  # login/logout
    path("accounts/", include("accounts.urls")),
    path("accounts/signup/", signup_view, name="signup_view"),  # signup
]
