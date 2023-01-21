import random

from django.core.management.base import BaseCommand

from apps.faction.models.culture import Culture
from apps.item.models.item_type import ItemType
from apps.marketplace.models.marketplace import Marketplace
from apps.skirmish.services.generators.item import ItemGenerator
from apps.skirmish.services.generators.warrior import WarriorGenerator


class Command(BaseCommand):
    def handle(self, *args, **options):
        marketplace = Marketplace.objects.all().first()

        weapon_generator = ItemGenerator(faction=None, item_type=ItemType.FunctionChoices.FUNCTION_WEAPON)
        armor_generator = ItemGenerator(faction=None, item_type=ItemType.FunctionChoices.FUNCTION_WEAPON)
        warrior_generator = WarriorGenerator(culture=Culture.objects.all().order_by("?").first(), faction=None)

        marketplace.available_items.add(*[weapon_generator.process() for x in range(random.randrange(1, 3))])
        marketplace.available_items.add(*[armor_generator.process() for x in range(random.randrange(1, 3))])
        marketplace.available_mercenaries.add(*[warrior_generator.process() for x in range(random.randrange(3, 5))])
