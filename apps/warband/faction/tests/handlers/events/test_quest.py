import pytest

from apps.warband.faction.handlers.events.quest import handle_quest_warrior
from apps.warband.faction.messages.commands.warrior import RecruitWarriorFromQuest
from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.quest.messages.events.quest_contract import QuestContractReturned
from apps.warband.quest.quests.fetch_a_good_warrior import FetchAGoodWarrior
from apps.warband.quest.quests.harvest_hands import HarvestHands
from apps.warband.quest.tests.factories.quest_contract import QuestContractFactory
from apps.warband.skirmish.tests.factories.warrior import WarriorFactory
from apps.warband.warrior.services.generators.warrior.champion import ChampionWarriorGenerator


@pytest.mark.django_db
def test_handle_quest_warrior_brings_the_man_home():
    faction = FactionFactory()

    result = handle_quest_warrior(
        context=QuestContractReturned(
            faction=faction,
            quest_contract=QuestContractFactory(faction=faction),
            warriors=[WarriorFactory(faction=faction)],
            outcome=FetchAGoodWarrior.OUTCOMES[0],
            month=3,
        )
    )

    assert result == RecruitWarriorFromQuest(faction=faction, generator_class=ChampionWarriorGenerator, month=3)


@pytest.mark.django_db
def test_handle_quest_warrior_for_an_outcome_bringing_nobody():
    faction = FactionFactory()

    result = handle_quest_warrior(
        context=QuestContractReturned(
            faction=faction,
            quest_contract=QuestContractFactory(faction=faction),
            warriors=[WarriorFactory(faction=faction)],
            outcome=HarvestHands.OUTCOMES[0],
            month=3,
        )
    )

    assert result is None
