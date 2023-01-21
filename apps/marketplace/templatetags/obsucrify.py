from django import template

register = template.Library()


@register.filter
def obscurify(value: int, avg_value: int) -> str:
    if value * 1.2 > avg_value:
        return "High"
    elif value * 0.8 < avg_value:
        return "Low"
    return "Mediocre"
