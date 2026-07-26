import factory
from factory.django import DjangoModelFactory

from apps.item.models.item import Item
from apps.item.tests.factories.item_type import ItemTypeFactory
from apps.savegame.tests.factories.savegame import SavegameFactory


class ItemFactory(DjangoModelFactory):
    class Meta:
        model = Item

    type = factory.SubFactory(ItemTypeFactory)
    condition = Item.ConditionChoices.CONDITION_TRADITIONAL
    price = 100
    modifier = 0
    savegame = factory.SubFactory(SavegameFactory)
    # Unowned items are the ones lying in the town shop
    owner = None
