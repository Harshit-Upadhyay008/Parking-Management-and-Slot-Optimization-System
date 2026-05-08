from django import template

register = template.Library()

@register.filter
def subtract(value, arg):
    return value - arg

@register.filter
def percentage(value, total):
    if total == 0:
        return 0
    return round((value / total) * 100, 1)
