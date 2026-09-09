import pytest

from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.quest.tests.factories.quest_contract import QuestContractFactory
from apps.warband.skirmish.tests.factories.warrior import WarriorFactory
from apps.warband.warrior.services.dismissal import (
    BUSY_REFUSAL,
    LEADER_REFUSAL,
    UNAFFORDABLE_REFUSAL,
    get_dismissal_refusals,
)


@pytest.mark.django_db
def test_get_dismissal_refusals_lets_a_free_warrior_go():
    faction = FactionFactory()
    warrior = WarriorFactory(faction=faction, monthly_salary=120)

    result = get_dismissal_refusals(faction=faction, warrior_list=[warrior], month=3, balance=1000)

    assert result == {}


@pytest.mark.django_db
def test_get_dismissal_refusals_keeps_the_leader():
    faction = FactionFactory()
    leader = WarriorFactory(faction=faction, monthly_salary=120)
    faction.leader = leader
    faction.save()

    result = get_dismissal_refusals(faction=faction, warrior_list=[leader], month=3, balance=1000)

    assert result == {leader.id: LEADER_REFUSAL}


@pytest.mark.django_db
def test_get_dismissal_refusals_keeps_a_warrior_signed_on_to_a_quest():
    """
    "exclude_currently_busy" is the game's definition of busy, and a man dismissed out of a fight
    leaves a skirmish roster pointing at a warrior with no faction.
    """
    faction = FactionFactory()
    warrior = WarriorFactory(faction=faction, monthly_salary=120)
    quest_contract = QuestContractFactory(faction=faction, accepted_in_month=3)
    quest_contract.assigned_warriors.add(warrior)

    result = get_dismissal_refusals(faction=faction, warrior_list=[warrior], month=3, balance=1000)

    assert result == {warrior.id: BUSY_REFUSAL}


@pytest.mark.django_db
def test_get_dismissal_refusals_names_the_month_before_the_price():
    """
    The month ends on its own and the price is the one the player can go and raise silver for, so a
    man who trips both is told about the month rather than sent off to sell something he may not
    spend the proceeds of yet.
    """
    faction = FactionFactory()
    warrior = WarriorFactory(faction=faction, monthly_salary=120)
    quest_contract = QuestContractFactory(faction=faction, accepted_in_month=3)
    quest_contract.assigned_warriors.add(warrior)

    result = get_dismissal_refusals(faction=faction, warrior_list=[warrior], month=3, balance=0)

    assert result == {warrior.id: BUSY_REFUSAL}


@pytest.mark.django_db
def test_get_dismissal_refusals_on_a_purse_that_cannot_pay_him_off():
    faction = FactionFactory()
    warrior = WarriorFactory(faction=faction, monthly_salary=120)

    result = get_dismissal_refusals(faction=faction, warrior_list=[warrior], month=3, balance=119)

    assert result == {warrior.id: UNAFFORDABLE_REFUSAL}


@pytest.mark.django_db
def test_get_dismissal_refusals_answers_a_whole_roster_at_once():
    """
    Asked per roster rather than per man, because the page offering the control renders a card each
    and a lookup per card is a query per card.
    """
    faction = FactionFactory()
    leader = WarriorFactory(faction=faction, monthly_salary=120)
    faction.leader = leader
    faction.save()
    free_warrior = WarriorFactory(faction=faction, monthly_salary=120)

    result = get_dismissal_refusals(faction=faction, warrior_list=[leader, free_warrior], month=3, balance=1000)

    assert result == {leader.id: LEADER_REFUSAL}
