import json

from django import template

register = template.Library()


@register.filter
def to_json(value):
    """Serialize a Python value to a JSON string for use in HTML data attributes."""
    return json.dumps(value or {})
