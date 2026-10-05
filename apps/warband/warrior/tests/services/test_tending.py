import pytest

from apps.warband.faction.models.faction import Faction
from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.skirmish.models.warrior import Warrior
from apps.warband.skirmish.tests.factories.skirmish import SkirmishFactory
from apps.warband.skirmish.tests.factories.warrior import WarriorFactory
from apps.warband.town.models import Town
from apps.warband.warrior.services.tending import (
    ALREADY_TENDED_THIS_MONTH_REFUSAL,
    DEAD_REFUSAL,
    NO_SANCTUARY_REFUSAL,
    NOT_YOUR_MAN_REFUSAL,
    OPEN_FIGHT_REFUSAL,
    UNAFFORDABLE_REFUSAL,
    UNWOUNDED_REFUSAL,
    get_tending_price,
    get_tending_refusal,
    was_tended,
)


def _faction_with_sanctuary(level: int = Town.SanctuaryChoices.SANCTUARY_SMALL) -> Faction:
    return FactionFactory(town__sanctuary=level)


@pytest.mark.parametrize(
    ("level", "price"),
    [
        (Town.SanctuaryChoices.SANCTUARY_SMALL, 150),
        (Town.SanctuaryChoices.SANCTUARY_MEDIUM, 120),
        (Town.SanctuaryChoices.SANCTUARY_LARGE, 90),
    ],
)
@pytest.mark.django_db
def test_get_tending_price_is_per_point_missing_at_the_towns_sanctuary(level, price):
    faction = _faction_with_sanctuary(level=level)
    warrior = WarriorFactory(faction=faction, current_health=10, max_health=40)

    result = get_tending_price(warrior=warrior, town=faction.town)

    assert result == price


@pytest.mark.django_db
def test_get_tending_refusal_lets_a_wounded_man_be_tended():
    faction = _faction_with_sanctuary()
    warrior = WarriorFactory(faction=faction, current_health=10, max_health=40)

    result = get_tending_refusal(warrior=warrior, faction=faction, month=3, balance=150)

    assert result is None


@pytest.mark.django_db
def test_get_tending_refusal_wakes_nobody_from_the_dead():
    faction = _faction_with_sanctuary()
    warrior = WarriorFactory(
        faction=faction, current_health=0, max_health=40, condition=Warrior.ConditionChoices.CONDITION_DEAD
    )

    result = get_tending_refusal(warrior=warrior, faction=faction, month=3, balance=1000)

    assert result == DEAD_REFUSAL


@pytest.mark.django_db
def test_get_tending_refusal_turns_away_a_captive():
    """
    A captive has no faction, and keeps mending from his captor's sanctuary month by month.
    """
    faction = _faction_with_sanctuary()
    warrior = WarriorFactory(
        faction=None, savegame=faction.savegame, culture=faction.culture, current_health=10, max_health=40
    )
    faction.captured_warriors.add(warrior)

    result = get_tending_refusal(warrior=warrior, faction=faction, month=3, balance=1000)

    assert result == NOT_YOUR_MAN_REFUSAL


@pytest.mark.django_db
def test_get_tending_refusal_turns_away_a_rivals_man():
    faction = _faction_with_sanctuary()
    warrior = WarriorFactory(faction=FactionFactory(), current_health=10, max_health=40)

    result = get_tending_refusal(warrior=warrior, faction=faction, month=3, balance=1000)

    assert result == NOT_YOUR_MAN_REFUSAL


@pytest.mark.django_db
def test_get_tending_refusal_has_nothing_to_sell_a_whole_man():
    faction = _faction_with_sanctuary()
    warrior = WarriorFactory(faction=faction, current_health=40, max_health=40)

    result = get_tending_refusal(warrior=warrior, faction=faction, month=3, balance=1000)

    assert result == UNWOUNDED_REFUSAL


@pytest.mark.django_db
def test_get_tending_refusal_without_a_sanctuary():
    faction = _faction_with_sanctuary(level=Town.SanctuaryChoices.SANCTUARY_NONE)
    warrior = WarriorFactory(faction=faction, current_health=10, max_health=40)

    result = get_tending_refusal(warrior=warrior, faction=faction, month=3, balance=1000)

    assert result == NO_SANCTUARY_REFUSAL


@pytest.mark.django_db
def test_get_tending_refusal_while_he_stands_in_an_open_fight():
    faction = _faction_with_sanctuary()
    warrior = WarriorFactory(faction=faction, current_health=10, max_health=40)
    skirmish = SkirmishFactory(attacking_faction=faction, victorious_faction=None)
    skirmish.attacking_warriors.add(warrior)

    result = get_tending_refusal(warrior=warrior, faction=faction, month=3, balance=1000)

    assert result == OPEN_FIGHT_REFUSAL


@pytest.mark.django_db
def test_get_tending_refusal_once_a_month():
    faction = _faction_with_sanctuary()
    warrior = WarriorFactory(faction=faction, current_health=10, max_health=40, last_tended_at=3)

    result = get_tending_refusal(warrior=warrior, faction=faction, month=3, balance=1000)

    assert result == ALREADY_TENDED_THIS_MONTH_REFUSAL


@pytest.mark.django_db
def test_get_tending_refusal_short_of_the_price():
    faction = _faction_with_sanctuary()
    warrior = WarriorFactory(faction=faction, current_health=10, max_health=40)

    result = get_tending_refusal(warrior=warrior, faction=faction, month=3, balance=149)

    assert result == UNAFFORDABLE_REFUSAL


@pytest.mark.django_db
def test_get_tending_refusal_names_the_month_before_the_price():
    """
    The month ends on its own and the price is the one the player can go and raise silver for.
    """
    faction = _faction_with_sanctuary()
    warrior = WarriorFactory(faction=faction, current_health=10, max_health=40, last_tended_at=3)

    result = get_tending_refusal(warrior=warrior, faction=faction, month=3, balance=0)

    assert result == ALREADY_TENDED_THIS_MONTH_REFUSAL


@pytest.mark.django_db
def test_was_tended_reads_the_month_off_the_row():
    warrior = WarriorFactory(last_tended_at=3)

    assert (was_tended(warrior=warrior, month=3), was_tended(warrior=warrior, month=4)) == (True, False)
