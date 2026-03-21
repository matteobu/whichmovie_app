from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = (
        "username",
        "email",
        "newsletter_opt_in",
        "is_staff",
        "is_active",
        "date_joined",
    )
    list_filter = ("is_staff", "is_active", "is_superuser", "newsletter_opt_in")
    search_fields = ("username", "email")
    ordering = ("-date_joined",)

    # Add newsletter_opt_in to the user edit form
    fieldsets = BaseUserAdmin.fieldsets + (
        ("Newsletter", {"fields": ("newsletter_opt_in",)}),
    )
