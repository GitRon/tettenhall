from django import template

register = template.Library()


@register.filter
def is_below_peak(maximum: int, peak: int | None) -> bool:  # noqa: PBR001
    """
    Whether a ceiling sits below the highest one the man has held. Health keeps no peak, so a missing
    one is never above anything.
    """
    return peak is not None and maximum < peak
