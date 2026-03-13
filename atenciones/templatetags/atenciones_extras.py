from django import template

register = template.Library()

@register.filter
def eq(value, arg):
    """
    Returns True if value == arg, else False
    Usage: {% if value|eq:arg %}
    """
    return value == arg
