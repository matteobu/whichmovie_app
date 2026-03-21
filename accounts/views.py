from allauth.account.views import PasswordChangeView
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse


@login_required
def profile_view(request):
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "toggle_newsletter":
            request.user.newsletter_opt_in = not request.user.newsletter_opt_in
            request.user.save()
            if request.user.newsletter_opt_in:
                messages.success(request, "You've subscribed to our newsletter.")
            else:
                messages.success(request, "You've unsubscribed from our newsletter.")
            return redirect("profile")
    return render(request, "account/profile.html")


class CustomPasswordChangeView(PasswordChangeView):
    def get_success_url(self):
        success_url = reverse("profile")
        return success_url
