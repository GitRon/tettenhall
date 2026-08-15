import pytest

from apps.faction.handlers.commands.warrior import (
    handle_draft_warrior_from_fyrd,
    handle_restock_pub_mercenaries,
    handle_warrior_monthly_salaries,
)
from apps.faction.messages.commands.faction import PayMonthlyWarriorSalaries
from apps.faction.messages.commands.warrior import DraftWarriorFromFyrd, RestockTownMercenaries
from apps.faction.messages.events.faction import MonthlyWarriorSalariesPaid, MonthlyWarriorSalariesUnpaid
from apps.faction.messages.events.warrior import RequestWarriorForPub, WarriorRecruited
from apps.faction.models.faction import Faction
from apps.faction.tests.factories.faction import FactionFactory
from apps.finance.tests.factories.transaction import TransactionFactory
from apps.skirmish.models import Warrior
from apps.skirmish.tests.factories.warrior import WarriorFactory
from apps.town.models import Town
from apps.warrior.services.generators.warrior.mercenary import MercenaryWarriorGenerator


def _player_faction(*, hall: int = Town.HallChoices.HALL_NONE) -> Faction:
    """
    A faction its own savegame points to as the player's.

    FactionFactory leaves "savegame.player_faction" unset, and only the player's town has a pub to
    restock, so a plain factory faction is skipped by the handler.
    """
    faction = FactionFactory(town__hall=hall)
    faction.savegame.player_faction = faction
    faction.savegame.save()

    return faction


@pytest.mark.django_db
def test_handle_restock_pub_mercenaries_requests_one_warrior_per_hall_slot():
    # A Great Hall offers two mercenary slots
    faction = _player_faction(hall=Town.HallChoices.HALL_MEDIUM)

    result = handle_restock_pub_mercenaries(context=RestockTownMercenaries(faction=faction, month=3))

    assert len(result) == 2
    assert result[0] == RequestWarriorForPub(
        savegame=faction.savegame,
        faction=None,
        # Drawn per slot with order_by("?"), so everything but the culture is deterministic
        culture=result[0].culture,
        generator_class=MercenaryWarriorGenerator,
        month=3,
    )


@pytest.mark.django_db
def test_handle_restock_pub_mercenaries_removes_previous_stock():
    faction = _player_faction()
    faction.available_mercenaries.add(WarriorFactory(faction=faction))

    handle_restock_pub_mercenaries(context=RestockTownMercenaries(faction=faction, month=3))

    assert faction.available_mercenaries.count() == 0


@pytest.mark.django_db
def test_handle_restock_pub_mercenaries_skips_a_rival_faction():
    """
    The requested mercenaries are generated without a faction of their own, so handle_add_warrior_to_pub
    can only ever stock the player's pub. Restocking a rival - which NewFactionCreated does for each
    of them - would therefore fill the player's pub a second time.
    """
    rival_faction = FactionFactory()
    previous_stock = WarriorFactory(faction=rival_faction)
    rival_faction.available_mercenaries.add(previous_stock)

    result = handle_restock_pub_mercenaries(context=RestockTownMercenaries(faction=rival_faction, month=3))

    assert result == []
    # Bailing out before the clean-up, so the rival keeps whatever it had
    assert list(rival_faction.available_mercenaries.all()) == [previous_stock]


@pytest.mark.django_db
def test_handle_draft_warrior_from_fyrd_with_filled_reserve():
    faction = FactionFactory(fyrd_reserve=3)

    result = handle_draft_warrior_from_fyrd(context=DraftWarriorFromFyrd(faction=faction, month=3))

    assert result == WarriorRecruited(
        faction=faction, warrior=Warrior.objects.get(faction=faction), recruitment_price=0, month=3
    )
    faction.refresh_from_db()
    assert faction.fyrd_reserve == 2


@pytest.mark.django_db
def test_handle_draft_warrior_from_fyrd_with_empty_reserve():
    faction = FactionFactory(fyrd_reserve=0)

    result = handle_draft_warrior_from_fyrd(context=DraftWarriorFromFyrd(faction=faction, month=3))

    assert result is None
    assert Warrior.objects.filter(faction=faction).exists() is False


@pytest.mark.django_db
def test_handle_warrior_monthly_salaries_pays_a_roster_the_purse_covers():
    faction = FactionFactory()
    TransactionFactory(faction=faction, amount=1000)
    warrior = WarriorFactory(faction=faction, monthly_salary=200, unpaid_months=2)

    result = handle_warrior_monthly_salaries(context=PayMonthlyWarriorSalaries(faction=faction, month=3))

    assert result == [MonthlyWarriorSalariesPaid(faction=faction, amount=200, month=3)]
    warrior.refresh_from_db()
    assert warrior.unpaid_months == 0


@pytest.mark.django_db
def test_handle_warrior_monthly_salaries_pays_the_cheapest_warriors_first():
    """
    Paying from the cheapest up fits the most men into whatever silver there is, so the shortfall
    lands on the veterans - the ones whose salary grew with every level.
    """
    faction = FactionFactory()
    TransactionFactory(faction=faction, amount=350)
    levy = WarriorFactory(faction=faction, monthly_salary=50)
    thegn = WarriorFactory(faction=faction, monthly_salary=200)
    ealdorman = WarriorFactory(faction=faction, monthly_salary=300)

    result = handle_warrior_monthly_salaries(context=PayMonthlyWarriorSalaries(faction=faction, month=3))

    assert result == [
        MonthlyWarriorSalariesPaid(faction=faction, amount=250, month=3),
        MonthlyWarriorSalariesUnpaid(faction=faction, warrior_list=[ealdorman], missing_amount=300, month=3),
    ]
    levy.refresh_from_db()
    thegn.refresh_from_db()
    assert (levy.unpaid_months, thegn.unpaid_months, result[1].warrior_list[0].unpaid_months) == (0, 0, 1)


@pytest.mark.django_db
def test_handle_warrior_monthly_salaries_stays_silent_about_the_nothing_it_paid():
    """
    An empty purse used to still announce "salaries of 0 silver paid", writing a zero transaction and
    a log line that contradicts the shortfall printed directly under it.
    """
    faction = FactionFactory()
    warrior = WarriorFactory(faction=faction, monthly_salary=50)

    result = handle_warrior_monthly_salaries(context=PayMonthlyWarriorSalaries(faction=faction, month=3))

    assert result == [MonthlyWarriorSalariesUnpaid(faction=faction, warrior_list=[warrior], missing_amount=50, month=3)]
    warrior.refresh_from_db()
    assert warrior.unpaid_months == 1


@pytest.mark.django_db
def test_handle_warrior_monthly_salaries_with_an_empty_roster():
    faction = FactionFactory()

    result = handle_warrior_monthly_salaries(context=PayMonthlyWarriorSalaries(faction=faction, month=3))

    assert result == []
