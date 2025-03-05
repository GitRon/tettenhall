from django.db.models import QuerySet

from apps.item.models.item_type import ItemType
from apps.item.services.generators.item.base import BaseItemGenerator


class LeaderItemGenerator(BaseItemGenerator):
    MODIFIER_ROLLS_MU = 4
    MODIFIER_ROLLS_SIGMA = 1

    def _get_queryset_for_type(self) -> QuerySet:
        # TODO: this is ugly
        if self.function == ItemType.FunctionChoices.FUNCTION_WEAPON:
            return (
                ItemType.objects.filter(function=self.function)
                .filter(name__in=["Battle axe", "Long sword"])
                .exclude(is_fallback=True)
                .order_by("?")
            )
        return ItemType.objects.filter(function=self.function).exclude(is_fallback=True).order_by("?")
