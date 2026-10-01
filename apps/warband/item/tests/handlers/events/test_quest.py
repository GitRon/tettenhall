import pytest

from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.item.handlers.events.quest import handle_quest_item
from apps.warband.item.messages.commands.item import CreateItem
from apps.warband.quest.messages.events.quest_contract import QuestContractReturned
from apps.warband.quest.quests.harvest_hands import HarvestHands
from apps.warband.quest.quests.seek_a_good_blade import SeekAGoodBlade
from apps.warband.quest.tests.factories.quest_contract import QuestContractFactory
from apps.warband.skirmish.tests.factories.warrior import WarriorFactory


@pytest.mark.django_db
def test_handle_quest_item_puts_the_find_in_the_stores():
    faction = FactionFactory()
    outcome = SeekAGoodBlade.OUTCOMES[0]

    result = handle_quest_item(
        context=QuestContractReturned(
            faction=faction,
            quest_contract=QuestContractFactory(faction=faction),
            warriors=[WarriorFactory(faction=faction)],
            outcome=outcome,
            month=3,
        )
    )

    assert result == CreateItem(
        owner=faction,
        faction=faction,
        generator_class=outcome.item_generator_class,
        item_function=outcome.item_function,
        month=3,
        quality_bonus=outcome.item_quality_bonus,
    )


@pytest.mark.django_db
def test_handle_quest_item_for_an_outcome_finding_nothing():
    faction = FactionFactory()

    result = handle_quest_item(
        context=QuestContractReturned(
            faction=faction,
            quest_contract=QuestContractFactory(faction=faction),
            warriors=[WarriorFactory(faction=faction)],
            outcome=HarvestHands.OUTCOMES[0],
            month=3,
        )
    )

    assert result is None
