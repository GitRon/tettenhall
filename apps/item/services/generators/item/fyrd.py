from django.db.models import QuerySet

from apps.item.models.item_type import ItemType
from apps.item.services.generators.item.base import BaseItemGenerator


class FyrdItemGenerator(BaseItemGenerator):
    MODIFIER_ROLLS_MU = 0
    MODIFIER_ROLLS_SIGMA = 2
    # Half of nothing is nothing, spelled out rather than left to inheritance: the base class carries a
    # mean of its own, and a levy who inherited it would come off the fields better armoured than armed
    ARMOR_MODIFIER_ROLLS_MU = 0
    ARMOR_MODIFIER_ROLLS_SIGMA = 2

    def _get_queryset_for_type(self) -> QuerySet:
        # TODO (#94): this is ugly
        if self.function == ItemType.FunctionChoices.FUNCTION_WEAPON:
            return (
                ItemType.objects.filter(function=self.function)
                .filter(name__in=["Pitchfork", "Spear"])
                .exclude(is_fallback=True)
                .order_by("?")
            )
        return ItemType.objects.filter(function=self.function).exclude(is_fallback=True).order_by("?")
