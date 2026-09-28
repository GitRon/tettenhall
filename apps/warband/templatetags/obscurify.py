from django import template

register = template.Library()

# How far off the average a value has to sit before it is called anything but mediocre
HIGH_SHARE = 1.2
LOW_SHARE = 0.8


@register.filter
def obscurify(value: int, avg_value: int) -> str:  # noqa: PBR001
    if value > avg_value * HIGH_SHARE:
        return "High"
    if value < avg_value * LOW_SHARE:
        return "Low"
    return "Mediocre"
