from allauth.account.views import PasswordChangeView
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.urls import reverse


@login_required
def profile_view(request):
    return render(request, "account/profile.html")


class CustomPasswordChangeView(PasswordChangeView):
    def get_success_url(self):
        success_url = reverse("profile")
        return success_url
