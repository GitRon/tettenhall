import factory
from factory.django import DjangoModelFactory

from apps.item.models.item import Item


class ItemFactory(DjangoModelFactory):
    class Meta:
        model = Item

    condition = Item.ConditionChoices.CONDITION_TRADITIONAL
    price = 10
    modifier = 0
    owner = None

    @factory.post_generation
    def type(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            self.type = extracted
