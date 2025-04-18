from django import template

register = template.Library()


@register.filter
def obscurify(value: int, avg_value: int) -> str:  # noqa: PBR001
    if value * 1.2 > avg_value:
        return "High"
    if value * 0.8 < avg_value:
        return "Low"
    return "Mediocre"
