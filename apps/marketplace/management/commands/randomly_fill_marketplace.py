import random

from django.core.management.base import BaseCommand

from apps.faction.models.culture import Culture
from apps.item.models.item import Item
from apps.item.models.item_type import ItemType
from apps.marketplace.models.marketplace import Marketplace
from apps.skirmish.models.warrior import Warrior
from apps.skirmish.services.generators.item import ItemGenerator
from apps.skirmish.services.generators.warrior import WarriorGenerator


class Command(BaseCommand):
    def handle(self, *args, **options):
        marketplace = Marketplace.objects.all().first()

        # Clean up
        Warrior.objects.filter(faction__isnull=True).delete()
        Item.objects.filter(owner__isnull=True).delete()

        no_warriors = random.randrange(2, 4)
        for _ in range(no_warriors):
            warrior_generator = WarriorGenerator(culture=Culture.objects.all().order_by("?").first(), faction=None)
            marketplace.available_mercenaries.add(warrior_generator.process())

        no_items = random.randrange(4, 6)
        for _ in range(no_items):
            if bool(random.getrandbits(1)):
                item_generator = ItemGenerator(faction=None, item_type=ItemType.FunctionChoices.FUNCTION_WEAPON)
            else:
                item_generator = ItemGenerator(faction=None, item_type=ItemType.FunctionChoices.FUNCTION_ARMOR)

            marketplace.available_items.add(item_generator.process())
