from django.core.management.base import BaseCommand
from django.db.models import F

from apps.skirmish.models.battle_history import BattleHistory
from apps.skirmish.models.skirmish import Skirmish
from apps.skirmish.models.warrior import Warrior


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("skirmish_id", nargs="+", type=int)

    def handle(self, *args, **options):
        skirmish = Skirmish.objects.get(id=options["skirmish_id"][0])

        skirmish.current_round = 1
        skirmish.victorious_faction = None
        skirmish.save()

        skirmish.player_warriors.update(
            current_health=F("max_health"), condition=Warrior.ConditionChoices.CONDITION_HEALTHY
        )
        skirmish.non_player_warriors.update(
            current_health=F("max_health"), condition=Warrior.ConditionChoices.CONDITION_HEALTHY
        )

        BattleHistory.objects.filter(skirmish=skirmish).delete()
