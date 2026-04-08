from allauth.account.forms import ResetPasswordForm, SignupForm
from django import forms
from django.contrib.auth import get_user_model
from django_recaptcha.fields import ReCaptchaField
from django_recaptcha.widgets import ReCaptchaV2Checkbox

User = get_user_model()


class CustomSignupForm(SignupForm):
    newsletter_opt_in = forms.BooleanField(
        required=False,
        label="Subscribe to newsletter",
        help_text="Receive movie recommendations and updates via email.",
    )
    captcha = ReCaptchaField(widget=ReCaptchaV2Checkbox())
    # Honeypot field - should remain empty, bots will fill it
    website = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"autocomplete": "off", "tabindex": "-1"}),
    )

    def clean_website(self):
        """Reject form submission if honeypot field is filled."""
        value = self.cleaned_data.get("website", "")
        if value:
            raise forms.ValidationError("Bot detected.")
        return value

    def save(self, request):
        user = super().save(request)
        user.newsletter_opt_in = self.cleaned_data.get("newsletter_opt_in", False)
        user.save()
        return user


class CustomResetPasswordForm(ResetPasswordForm):
    """Custom password reset form with CAPTCHA and honeypot protection."""

    captcha = ReCaptchaField(widget=ReCaptchaV2Checkbox())
    # Honeypot field - should remain empty, bots will fill it
    website = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"autocomplete": "off", "tabindex": "-1"}),
    )

    def clean_website(self):
        """Reject form submission if honeypot field is filled."""
        value = self.cleaned_data.get("website", "")
        if value:
            raise forms.ValidationError("Bot detected.")
        return value
