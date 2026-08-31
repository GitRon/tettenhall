from django import template

register = template.Library()


@register.filter
def obscurify(value: int, avg_value: int) -> str:  # noqa: PBR001
    if value > avg_value * 1.2:
        return "High"
    if value < avg_value * 0.8:
        return "Low"
    return "Mediocre"
