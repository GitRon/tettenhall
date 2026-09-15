import pytest

from apps.warband.faction.messages.events.faction import MonthlyWarriorSalariesUnpaid
from apps.warband.faction.messages.events.warrior import WarriorMonthPrepared
from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.skirmish.models.warrior import Warrior
from apps.warband.skirmish.tests.factories.warrior import WarriorFactory
from apps.warband.warrior.handlers.events.faction import (
    handle_heal_a_wounded_warrior_for_new_month,
    handle_replenish_a_warriors_morale_for_new_month,
    handle_unpaid_warriors,
)
from apps.warband.warrior.messages.commands.warrior import (
    HealInjuredWarrior,
    PunishUnpaidWarrior,
    ReplenishWarriorMorale,
)


@pytest.mark.django_db
def test_handle_unpaid_warriors_asks_for_one_punishment_per_man():
    """
    One command per warrior rather than one for the list, because what happens to him depends on how
    long he has gone without - and reading that off the roster is not something an event handler may
    do under strict mode.
    """
    faction = FactionFactory()
    thegn = WarriorFactory(faction=faction)
    ealdorman = WarriorFactory(faction=faction)

    result = handle_unpaid_warriors(
        context=MonthlyWarriorSalariesUnpaid(
            faction=faction, warrior_list=[thegn, ealdorman], missing_amount=500, month=3
        )
    )

    assert result == [
        PunishUnpaidWarrior(warrior=thegn, faction=faction, month=3),
        PunishUnpaidWarrior(warrior=ealdorman, faction=faction, month=3),
    ]


@pytest.mark.django_db
def test_handle_heal_a_wounded_warrior_for_new_month_asks_for_the_mending():
    faction = FactionFactory()
    wounded_warrior = WarriorFactory(faction=faction, current_health=5, max_health=20)

    result = handle_heal_a_wounded_warrior_for_new_month(
        context=WarriorMonthPrepared(faction=faction, warrior=wounded_warrior, month=3)
    )

    assert result == HealInjuredWarrior(faction=faction, warrior=wounded_warrior, month=3)


@pytest.mark.django_db
def test_handle_heal_a_wounded_warrior_for_new_month_passes_over_a_man_at_full_health():
    """
    The filter that used to be a queryset's. Asking the healing handler anyway would have it draw a
    random number of points and discard every one of them.
    """
    faction = FactionFactory()
    unhurt_warrior = WarriorFactory(faction=faction, current_health=20, max_health=20)

    result = handle_heal_a_wounded_warrior_for_new_month(
        context=WarriorMonthPrepared(faction=faction, warrior=unhurt_warrior, month=3)
    )

    assert result is None


@pytest.mark.django_db
def test_handle_heal_a_wounded_warrior_for_new_month_mends_a_captive():
    """
    Health is what a captor can mend, so a prisoner heals from his captor's month - no comparison
    against the faction on the event, unlike the morale reaction beside it.

    The captor is passed on because a captive's own faction is None: it is his captor's sanctuary
    doing the mending and his captor's month log the line belongs in.
    """
    captor = FactionFactory()
    captive = WarriorFactory(
        faction=None,
        savegame=captor.savegame,
        culture=captor.culture,
        current_health=5,
        max_health=20,
        condition=Warrior.ConditionChoices.CONDITION_UNCONSCIOUS,
    )

    result = handle_heal_a_wounded_warrior_for_new_month(
        context=WarriorMonthPrepared(faction=captor, warrior=captive, month=3)
    )

    assert result == HealInjuredWarrior(faction=captor, warrior=captive, month=3)


@pytest.mark.django_db
def test_handle_replenish_a_warriors_morale_for_new_month_asks_for_the_refill():
    faction = FactionFactory()
    shaken_warrior = WarriorFactory(faction=faction, current_morale=5, max_morale=20)

    result = handle_replenish_a_warriors_morale_for_new_month(
        context=WarriorMonthPrepared(faction=faction, warrior=shaken_warrior, month=3)
    )

    assert result == ReplenishWarriorMorale(warrior=shaken_warrior, month=3)


@pytest.mark.django_db
def test_handle_replenish_a_warriors_morale_for_new_month_passes_over_a_captive():
    """
    Spirit is not something a captor can mend, and the refill goes to the maximum - so a month in an
    enemy cell would otherwise restore a man completely.

    His own faction against the one holding him is the one rule this handler cannot take from the
    event alone, capture having cleared the former.
    """
    captor = FactionFactory()
    captive = WarriorFactory(
        faction=None,
        savegame=captor.savegame,
        culture=captor.culture,
        current_morale=5,
        max_morale=20,
        condition=Warrior.ConditionChoices.CONDITION_UNCONSCIOUS,
    )

    result = handle_replenish_a_warriors_morale_for_new_month(
        context=WarriorMonthPrepared(faction=captor, warrior=captive, month=3)
    )

    assert result is None


@pytest.mark.django_db
def test_handle_replenish_a_warriors_morale_for_new_month_passes_over_an_unpaid_warrior():
    """
    The invariant "test_finish_month_view_keeps_an_unpaid_warriors_morale_down" pins from the other
    end: the refill is to the maximum, so without this guard every point insolvency had just taken
    would come straight back in the month it was taken.
    """
    faction = FactionFactory()
    unpaid_warrior = WarriorFactory(faction=faction, current_morale=5, max_morale=20, unpaid_months=1)

    result = handle_replenish_a_warriors_morale_for_new_month(
        context=WarriorMonthPrepared(faction=faction, warrior=unpaid_warrior, month=3)
    )

    assert result is None


@pytest.mark.django_db
def test_handle_replenish_a_warriors_morale_for_new_month_reaches_a_warrior_ordered_to_flee():
    """
    The freeze #43 closed, reachable again through a deliberate retreat unless the withdrawal leaves a
    man the way a rout does.

    This refill is the only road to "replenish_current_morale", which is the only thing that clears
    FLEEING. Only a man below his ceiling is taken, so a warrior merely charged a point off that
    ceiling - and therefore clamped to it - would never be reached again.
    """
    faction = FactionFactory()
    warrior = WarriorFactory(faction=faction, current_morale=20, max_morale=20)
    Warrior.objects.withdraw_from_the_fight(obj=warrior, lost_max_morale=1)

    result = handle_replenish_a_warriors_morale_for_new_month(
        context=WarriorMonthPrepared(faction=faction, warrior=warrior, month=3)
    )

    assert result == ReplenishWarriorMorale(warrior=warrior, month=3)


@pytest.mark.django_db
def test_handle_replenish_a_warriors_morale_for_new_month_picks_up_a_fleeing_warrior():
    """
    The half of the rally this reaction owns. Restoring the condition further down the chain only ever
    helps if the man who routed is asked for at all, and a warrior who fled without a scratch is
    reached by nothing else - the healing reaction wants the wounded, and he is not.
    """
    faction = FactionFactory()
    fleeing_warrior = WarriorFactory(
        faction=faction,
        current_morale=0,
        max_morale=20,
        condition=Warrior.ConditionChoices.CONDITION_FLEEING,
    )

    result = handle_replenish_a_warriors_morale_for_new_month(
        context=WarriorMonthPrepared(faction=faction, warrior=fleeing_warrior, month=3)
    )

    assert result == ReplenishWarriorMorale(warrior=fleeing_warrior, month=3)


@pytest.mark.django_db
def test_handle_replenish_a_warriors_morale_for_new_month_passes_over_a_man_at_full_morale():
    faction = FactionFactory()
    steady_warrior = WarriorFactory(faction=faction, current_morale=20, max_morale=20)

    result = handle_replenish_a_warriors_morale_for_new_month(
        context=WarriorMonthPrepared(faction=faction, warrior=steady_warrior, month=3)
    )

    assert result is None
