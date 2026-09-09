import factory
from factory.django import DjangoModelFactory

from apps.warband.item.models.item import Item
from apps.warband.item.tests.factories.item_type import ItemTypeFactory
from apps.warband.savegame.tests.factories.savegame import SavegameFactory


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
