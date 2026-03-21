from allauth.account.forms import SignupForm
from django import forms
from django.contrib.auth import get_user_model

User = get_user_model()


class CustomSignupForm(SignupForm):
    newsletter_opt_in = forms.BooleanField(
        required=False,
        label="Subscribe to newsletter",
        help_text="Receive movie recommendations and updates via email.",
    )

    def save(self, request):
        user = super().save(request)
        user.newsletter_opt_in = self.cleaned_data.get("newsletter_opt_in", False)
        user.save()
        return user
