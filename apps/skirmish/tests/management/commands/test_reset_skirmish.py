import pytest
from django.core.management import call_command

from apps.skirmish.models.skirmish import Skirmish
from apps.skirmish.models.warrior import Warrior
from apps.skirmish.tests.factories.battle_history import BattleHistoryFactory
from apps.skirmish.tests.factories.skirmish import SkirmishFactory
from apps.skirmish.tests.factories.warrior import WarriorFactory


@pytest.fixture
def fought_skirmish(db) -> Skirmish:
    """
    A skirmish in the state the developer tool is meant to undo: fought, decided and logged.
    """
    skirmish = SkirmishFactory(current_round=4)
    skirmish.victorious_faction = skirmish.attacking_faction
    skirmish.save()

    skirmish.attacking_warriors.add(
        WarriorFactory(
            faction=skirmish.attacking_faction,
            current_health=3,
            current_morale=1,
            condition=Warrior.ConditionChoices.CONDITION_FLEEING,
        )
    )
    skirmish.defending_warriors.add(
        WarriorFactory(
            faction=skirmish.defending_faction,
            current_health=-2,
            current_morale=0,
            condition=Warrior.ConditionChoices.CONDITION_UNCONSCIOUS,
        )
    )

    return skirmish


def test_reset_skirmish_rewinds_the_skirmish(fought_skirmish):
    call_command("reset_skirmish", fought_skirmish.id)

    fought_skirmish.refresh_from_db()
    assert fought_skirmish.current_round == 1
    assert fought_skirmish.victorious_faction is None


def test_reset_skirmish_heals_every_participant(fought_skirmish):
    call_command("reset_skirmish", fought_skirmish.id)

    healed_warriors = Warrior.objects.filter(
        id__in=(
            fought_skirmish.attacking_warriors.values_list("id", flat=True).union(
                fought_skirmish.defending_warriors.values_list("id", flat=True)
            )
        )
    )
    assert [warrior.condition for warrior in healed_warriors] == [
        Warrior.ConditionChoices.CONDITION_HEALTHY,
        Warrior.ConditionChoices.CONDITION_HEALTHY,
    ]
    assert [warrior.current_health == warrior.max_health for warrior in healed_warriors] == [True, True]


def test_reset_skirmish_releases_the_captives(fought_skirmish):
    captured_warrior = WarriorFactory(savegame=fought_skirmish.attacking_faction.savegame)
    fought_skirmish.attacking_faction.captured_warriors.add(captured_warrior)

    call_command("reset_skirmish", fought_skirmish.id)

    assert list(fought_skirmish.attacking_faction.captured_warriors.all()) == []


def test_reset_skirmish_clears_the_battle_history(fought_skirmish):
    BattleHistoryFactory(skirmish=fought_skirmish)

    call_command("reset_skirmish", fought_skirmish.id)

    assert fought_skirmish.battle_logs.count() == 0
