from django import template

register = template.Library()


@register.filter
def lookup(d, key) -> object:
    return d[key]
