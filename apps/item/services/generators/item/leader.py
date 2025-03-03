from django.db.models import QuerySet

from apps.item.models.item_type import ItemType
from apps.item.services.generators.item.base import BaseItemGenerator


class LeaderItemGenerator(BaseItemGenerator):
    MODIFIER_ROLLS_MU = 4
    MODIFIER_ROLLS_SIGMA = 1

    def _get_queryset_for_type(self) -> QuerySet:
        # TODO: this will never return an armor because of the name WHERE, right?
        return (
            ItemType.objects.filter(function=self.function, name__in=["Battle axe", "Long sword"])
            .exclude(is_fallback=True)
            .order_by("?")
        )
