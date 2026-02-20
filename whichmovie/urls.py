from django.contrib import admin
from django.urls import include, path

from accounts.views import CustomPasswordChangeView

from . import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.home, name="home"),  # landing page
    path("movies/", include("movies.urls")),  # movies page
    path("accounts/", include("accounts.urls")),  # custom view for signup/profile
    path("accounts/password/change/", CustomPasswordChangeView.as_view()),
    path("accounts/", include("allauth.urls")),
]
