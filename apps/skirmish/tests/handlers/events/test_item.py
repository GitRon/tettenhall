import pytest

from apps.skirmish.handlers.events.item import handle_distribute_loot
from apps.skirmish.messages.commands.item import WarriorDropsLoot
from apps.skirmish.messages.commands.transaction import WarriorDropsSilver
from apps.skirmish.messages.events.skirmish import SkirmishFinished
from apps.skirmish.models.warrior import Warrior
from apps.skirmish.tests.factories.skirmish import SkirmishFactory
from apps.skirmish.tests.factories.warrior import WarriorFactory


@pytest.mark.django_db
def test_handle_distribute_loot_hands_items_and_silver_of_every_incapacitated_warrior_to_the_victor():
    skirmish = SkirmishFactory()
    skirmish.victorious_faction = skirmish.attacking_faction
    skirmish.save()
    dead_enemy_warrior = WarriorFactory(
        faction=skirmish.defending_faction, condition=Warrior.ConditionChoices.CONDITION_DEAD
    )

    result = handle_distribute_loot(
        context=SkirmishFinished(
            skirmish=skirmish,
            incapacitated_warriors=[dead_enemy_warrior],
            defeated_unconscious_warriors=[],
            victorious_healthy_warriors=[],
            quest_name="Raid",
            quest_loot=250,
            month=3,
        )
    )

    assert result == [
        WarriorDropsLoot(skirmish=skirmish, warrior=dead_enemy_warrior, new_owner=skirmish.attacking_faction),
        WarriorDropsSilver(
            skirmish=skirmish,
            warrior=dead_enemy_warrior,
            gaining_faction=skirmish.attacking_faction,
            month=3,
        ),
    ]


@pytest.mark.django_db
def test_handle_distribute_loot_distributes_nothing_without_incapacitated_warriors():
    skirmish = SkirmishFactory()

    result = handle_distribute_loot(
        context=SkirmishFinished(
            skirmish=skirmish,
            incapacitated_warriors=[],
            defeated_unconscious_warriors=[],
            victorious_healthy_warriors=[],
            quest_name="Raid",
            quest_loot=250,
            month=3,
        )
    )

    assert result == []
