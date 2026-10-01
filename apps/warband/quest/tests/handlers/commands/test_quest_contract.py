from unittest import mock

import pytest

from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.quest.handlers.commands.quest_contract import handle_bring_quest_contracts_home
from apps.warband.quest.messages.commands.quest_contract import BringQuestContractsHome
from apps.warband.quest.messages.events.quest_contract import QuestContractLapsed, QuestContractReturned
from apps.warband.quest.models.quest_contract import QuestContract
from apps.warband.quest.quests.harvest_hands import HarvestHands
from apps.warband.quest.tests.factories.quest_contract import QuestContractFactory
from apps.warband.skirmish.models.warrior import Warrior
from apps.warband.skirmish.tests.factories.warrior import WarriorFactory


@pytest.mark.django_db
def test_handle_bring_quest_contracts_home_draws_what_the_men_brought():
    faction = FactionFactory()
    warrior = WarriorFactory(faction=faction)
    quest_contract = QuestContractFactory(faction=faction, accepted_in_month=2, assigned_warriors=[warrior])

    with mock.patch("apps.warband.quest.quests.base.random.choices", return_value=[HarvestHands.OUTCOMES[0]]):
        result = handle_bring_quest_contracts_home(context=BringQuestContractsHome(faction=faction, month=3))

    assert result == [
        QuestContractReturned(
            faction=faction,
            quest_contract=quest_contract,
            warriors=[warrior],
            outcome=HarvestHands.OUTCOMES[0],
            month=3,
        )
    ]
    assert QuestContract.objects.get(pk=quest_contract.pk).resolved_in_month == 3


@pytest.mark.django_db
def test_handle_bring_quest_contracts_home_shares_only_with_the_men_still_on_the_roster():
    faction = FactionFactory()
    warrior = WarriorFactory(faction=faction)
    dead_warrior = WarriorFactory(faction=faction, condition=Warrior.ConditionChoices.CONDITION_DEAD)
    walked_out_warrior = WarriorFactory(faction=None, savegame=faction.savegame, culture=faction.culture)
    QuestContractFactory(
        faction=faction, accepted_in_month=2, assigned_warriors=[warrior, dead_warrior, walked_out_warrior]
    )

    result = handle_bring_quest_contracts_home(context=BringQuestContractsHome(faction=faction, month=3))

    assert result[0].warriors == [warrior]


@pytest.mark.django_db
def test_handle_bring_quest_contracts_home_with_nobody_left_to_come_home():
    faction = FactionFactory()
    walked_out_warrior = WarriorFactory(faction=None, savegame=faction.savegame, culture=faction.culture)
    quest_contract = QuestContractFactory(faction=faction, accepted_in_month=2, assigned_warriors=[walked_out_warrior])

    result = handle_bring_quest_contracts_home(context=BringQuestContractsHome(faction=faction, month=3))

    assert result == [QuestContractLapsed(faction=faction, quest_contract=quest_contract, month=3)]


@pytest.mark.django_db
def test_handle_bring_quest_contracts_home_leaves_this_months_men_out():
    faction = FactionFactory()
    QuestContractFactory(faction=faction, accepted_in_month=3, assigned_warriors=[WarriorFactory(faction=faction)])

    result = handle_bring_quest_contracts_home(context=BringQuestContractsHome(faction=faction, month=3))

    assert result == []


@pytest.mark.django_db
def test_handle_bring_quest_contracts_home_when_another_month_turn_got_there_first():
    """The contract was still away when it was read, and resolved by the time its write landed."""
    faction = FactionFactory()
    QuestContractFactory(faction=faction, accepted_in_month=2, assigned_warriors=[WarriorFactory(faction=faction)])

    # A first-party mock, because the race is two requests apart: one test cannot read the contract
    # as still away and then have another month turn resolve it before the write
    with mock.patch.object(QuestContract.objects, "mark_resolved", return_value=False):
        result = handle_bring_quest_contracts_home(context=BringQuestContractsHome(faction=faction, month=3))

    assert result == []
