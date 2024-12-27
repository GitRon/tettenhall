from django import template

register = template.Library()


@register.filter
def lookup(d, key):  # noqa: PBR001, PBR002
    return d[key]
