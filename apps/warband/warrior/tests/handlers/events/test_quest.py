import pytest

from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.quest.messages.events.quest_contract import QuestContractReturned
from apps.warband.quest.quests.harvest_hands import HarvestHands
from apps.warband.quest.quests.kings_summons import KingsSummons
from apps.warband.quest.tests.factories.quest_contract import QuestContractFactory
from apps.warband.skirmish.tests.factories.warrior import WarriorFactory
from apps.warband.warrior.handlers.events.quest import handle_quest_renown
from apps.warband.warrior.messages.commands.warrior import GrantRenown


@pytest.mark.django_db
def test_handle_quest_renown_grants_every_man_who_came_home():
    faction = FactionFactory()
    first_warrior, second_warrior = WarriorFactory.create_batch(2, faction=faction)
    outcome = KingsSummons.OUTCOMES[0]

    result = handle_quest_renown(
        context=QuestContractReturned(
            faction=faction,
            quest_contract=QuestContractFactory(faction=faction),
            warriors=[first_warrior, second_warrior],
            outcome=outcome,
            month=3,
        )
    )

    assert result == [
        GrantRenown(warrior=first_warrior, faction=faction, renown=outcome.renown_per_man, month=3),
        GrantRenown(warrior=second_warrior, faction=faction, renown=outcome.renown_per_man, month=3),
    ]


@pytest.mark.django_db
def test_handle_quest_renown_for_an_outcome_paying_none():
    faction = FactionFactory()

    result = handle_quest_renown(
        context=QuestContractReturned(
            faction=faction,
            quest_contract=QuestContractFactory(faction=faction),
            warriors=[WarriorFactory(faction=faction)],
            outcome=HarvestHands.OUTCOMES[0],
            month=3,
        )
    )

    assert result is None
