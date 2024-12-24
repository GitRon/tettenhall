from django import template

register = template.Library()


@register.filter
def lookup(d, key):  # noqa: PBR001
    return d[key]
