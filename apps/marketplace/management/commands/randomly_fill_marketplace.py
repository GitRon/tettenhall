import random

from django.core.management.base import BaseCommand

from apps.faction.models.culture import Culture
from apps.item.models.item import Item
from apps.item.models.item_type import ItemType
from apps.item.services.generators.item.mercenary import MercenaryItemGenerator
from apps.marketplace.models.marketplace import Marketplace
from apps.skirmish.models.warrior import Warrior
from apps.warrior.services.generators.warrior.mercenary import MercenaryWarriorGenerator


class Command(BaseCommand):
    def handle(self, *args, **options):
        marketplace = Marketplace.objects.all().first()

        # Clean up
        Warrior.objects.filter(faction__isnull=True).delete()
        Item.objects.filter(owner__isnull=True).delete()

        no_warriors = random.randrange(2, 4)
        for _ in range(no_warriors):
            warrior_generator = MercenaryWarriorGenerator(
                culture=Culture.objects.all().order_by("?").first(), faction=None
            )
            warrior = warrior_generator.process()
            print(f"Warrior created: {warrior} ({warrior.culture})")
            marketplace.available_mercenaries.add(warrior)

        no_items = random.randrange(4, 6)
        for _ in range(no_items):
            if bool(random.getrandbits(1)):
                item_generator = MercenaryItemGenerator(
                    faction=None, item_function=ItemType.FunctionChoices.FUNCTION_WEAPON
                )
            else:
                item_generator = MercenaryItemGenerator(
                    faction=None, item_function=ItemType.FunctionChoices.FUNCTION_ARMOR
                )

            item = item_generator.process()
            print(f"Item created: {item}")
            marketplace.available_items.add(item)
