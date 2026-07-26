import factory
from factory.django import DjangoModelFactory

from apps.item.models.item_type import ItemType


class ItemTypeFactory(DjangoModelFactory):
    class Meta:
        model = ItemType

    name = factory.Sequence(lambda n: f"Item type {n}")
    function = ItemType.FunctionChoices.FUNCTION_WEAPON
    base_value = "1d6"
    svg_image_name = "sword"
    is_fallback = False
