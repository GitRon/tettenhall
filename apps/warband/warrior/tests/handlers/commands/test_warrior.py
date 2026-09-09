from unittest import mock

import pytest

from apps.warband.faction.handlers.commands.faction import handle_create_new_faction
from apps.warband.faction.messages.commands.faction import CreateNewFaction
from apps.warband.faction.messages.events.warrior import WarriorRecruited, WarriorWasSoldIntoSlavery
from apps.warband.faction.tests.factories.culture import CultureFactory
from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.item.models.item_type import ItemType
from apps.warband.item.tests.factories.item import ItemFactory
from apps.warband.item.tests.factories.item_type import ItemTypeFactory
from apps.warband.savegame.tests.factories.savegame import SavegameFactory
from apps.warband.skirmish.models.warrior import Warrior
from apps.warband.skirmish.tests.factories.warrior import WarriorFactory
from apps.warband.warrior.handlers.commands.warrior import (
    handle_change_warrior_max_morale,
    handle_dismiss_warrior,
    handle_enslave_captured_warrior,
    handle_heal_injured_warrior,
    handle_punish_unpaid_warrior,
    handle_recruit_captured_warrior,
    handle_replenish_warrior_morale,
)
from apps.warband.warrior.messages.commands.warrior import (
    ChangeWarriorMaxMorale,
    DismissWarrior,
    EnslaveCapturedWarrior,
    HealInjuredWarrior,
    PunishUnpaidWarrior,
    RecruitCapturedWarrior,
    ReplenishWarriorMorale,
)
from apps.warband.warrior.messages.events.warrior import (
    WarriorHealthHealed,
    WarriorLostMoraleOverUnpaidSalary,
    WarriorMaxMoraleChanged,
    WarriorMoraleReplenished,
    WarriorWalkedOutOverUnpaidSalary,
    WarriorWasDismissed,
)


@pytest.mark.django_db
def test_handle_replenish_warrior_morale_fills_up_to_the_maximum():
    warrior = WarriorFactory(current_morale=5, max_morale=20)

    result = handle_replenish_warrior_morale(context=ReplenishWarriorMorale(warrior=warrior, month=3))

    assert result == WarriorMoraleReplenished(warrior=warrior, faction=warrior.faction, recovered_morale=15, month=3)
    warrior.refresh_from_db()
    assert warrior.current_morale == 20


@pytest.mark.django_db
def test_handle_replenish_warrior_morale_does_nothing_on_full_morale():
    warrior = WarriorFactory(current_morale=20, max_morale=20)

    result = handle_replenish_warrior_morale(context=ReplenishWarriorMorale(warrior=warrior, month=3))

    assert result is None


@pytest.mark.django_db
def test_handle_heal_injured_warrior_heals_rolled_amount():
    warrior = WarriorFactory(current_health=5, max_health=20)

    with mock.patch("apps.warband.warrior.handlers.commands.warrior.random.randrange", return_value=5):
        result = handle_heal_injured_warrior(
            context=HealInjuredWarrior(faction=warrior.faction, warrior=warrior, month=3)
        )

    assert result == WarriorHealthHealed(warrior=warrior, faction=warrior.faction, healed_points=5, month=3)
    warrior.refresh_from_db()
    assert warrior.current_health == 10


@pytest.mark.django_db
def test_handle_heal_injured_warrior_caps_healing_at_the_maximum():
    warrior = WarriorFactory(current_health=18, max_health=20)

    with mock.patch("apps.warband.warrior.handlers.commands.warrior.random.randrange", return_value=5):
        result = handle_heal_injured_warrior(
            context=HealInjuredWarrior(faction=warrior.faction, warrior=warrior, month=3)
        )

    assert result == WarriorHealthHealed(warrior=warrior, faction=warrior.faction, healed_points=2, month=3)
    warrior.refresh_from_db()
    assert warrior.current_health == 20


@pytest.mark.django_db
def test_handle_heal_injured_warrior_at_full_health():
    warrior = WarriorFactory(current_health=20, max_health=20)

    with mock.patch("apps.warband.warrior.handlers.commands.warrior.random.randrange", return_value=5):
        result = handle_heal_injured_warrior(
            context=HealInjuredWarrior(faction=warrior.faction, warrior=warrior, month=3)
        )

    assert result is None


@pytest.mark.django_db
def test_handle_heal_injured_warrior_can_roll_the_maximum():
    """
    randrange() excludes its upper bound, so the maximum recoverable amount needs the "+ 1" to be
    reachable at all.
    """
    # A Shrine mends up to 8 points a month
    warrior = WarriorFactory(current_health=1, max_health=20, faction__town__sanctuary=1)

    with mock.patch(
        "apps.warband.warrior.handlers.commands.warrior.random.randrange", return_value=8
    ) as mocked_randrange:
        result = handle_heal_injured_warrior(
            context=HealInjuredWarrior(faction=warrior.faction, warrior=warrior, month=3)
        )

    mocked_randrange.assert_called_once_with(1, 9)
    assert result.healed_points == 8


@pytest.mark.django_db
def test_handle_heal_injured_warrior_heals_further_with_a_larger_sanctuary():
    """
    The sanctuary sets the ceiling of the monthly healing roll, so the building is what decides how
    fast a warrior comes back.
    """
    warrior = WarriorFactory(current_health=1, max_health=30, faction__town__sanctuary=3)

    with mock.patch(
        "apps.warband.warrior.handlers.commands.warrior.random.randrange", return_value=1
    ) as mocked_randrange:
        handle_heal_injured_warrior(context=HealInjuredWarrior(faction=warrior.faction, warrior=warrior, month=3))

    # A Great Sanctuary reaches 20 points, against the 4 a town without one manages
    mocked_randrange.assert_called_once_with(1, 21)


@pytest.mark.django_db
def test_handle_heal_injured_warrior_mends_a_rival_at_the_level_he_was_created_with():
    """
    The town a rival is actually created with, not one set up by hand: the ceiling a rival heals
    against is decided at faction creation and nothing ever raises it, so the two ends of that have
    to be checked together.
    """
    savegame = SavegameFactory()
    rival = handle_create_new_faction(
        context=CreateNewFaction(
            name="Mercia",
            town_name="Tamworth",
            culture_id=CultureFactory().id,
            savegame=savegame,
            is_player_faction=False,
        )
    ).faction
    warrior = WarriorFactory(faction=rival, savegame=savegame, current_health=1, max_health=20)

    with mock.patch(
        "apps.warband.warrior.handlers.commands.warrior.random.randrange", return_value=1
    ) as mocked_randrange:
        handle_heal_injured_warrior(context=HealInjuredWarrior(faction=rival, warrior=warrior, month=3))

    # A Shrine reaches 8 points, against the 4 a town without a sanctuary manages
    mocked_randrange.assert_called_once_with(1, 9)


@pytest.mark.django_db
def test_handle_heal_injured_warrior_mends_a_captive_at_his_captors_sanctuary():
    """
    A captive belongs to nobody, so the ceiling can only come from the faction holding him.
    """
    captor = FactionFactory(town__sanctuary=1)
    captive = WarriorFactory(
        faction=None,
        savegame=captor.savegame,
        culture=captor.culture,
        current_health=0,
        max_health=20,
        condition=Warrior.ConditionChoices.CONDITION_UNCONSCIOUS,
    )
    captor.captured_warriors.add(captive)

    with mock.patch(
        "apps.warband.warrior.handlers.commands.warrior.random.randrange", return_value=8
    ) as mocked_randrange:
        result = handle_heal_injured_warrior(context=HealInjuredWarrior(faction=captor, warrior=captive, month=3))

    # A Shrine mends up to 8 points a month, against the 4 of the town the captive no longer has
    mocked_randrange.assert_called_once_with(1, 9)
    assert result == WarriorHealthHealed(warrior=captive, faction=captor, healed_points=8, month=3)


@pytest.mark.django_db
def test_handle_heal_injured_warrior_wakes_a_captive_without_freeing_him():
    """
    Mending a captive above zero health lifts him out of CONDITION_UNCONSCIOUS, which is what makes
    him worth recruiting. He stays a prisoner all the same - every roster query goes through the
    faction he does not have, so being healthy buys him nothing while he is held.
    """
    captor = FactionFactory()
    captive = WarriorFactory(
        faction=None,
        savegame=captor.savegame,
        culture=captor.culture,
        current_health=0,
        max_health=20,
        condition=Warrior.ConditionChoices.CONDITION_UNCONSCIOUS,
    )
    captor.captured_warriors.add(captive)

    with mock.patch("apps.warband.warrior.handlers.commands.warrior.random.randrange", return_value=4):
        handle_heal_injured_warrior(context=HealInjuredWarrior(faction=captor, warrior=captive, month=3))

    captive.refresh_from_db()
    assert captive.condition == Warrior.ConditionChoices.CONDITION_HEALTHY
    assert list(captor.captured_warriors.all()) == [captive]


@pytest.mark.django_db
def test_handle_punish_unpaid_warrior_takes_a_quarter_of_his_morale():
    faction = FactionFactory()
    warrior = WarriorFactory(faction=faction, current_morale=20, max_morale=20, unpaid_months=1)

    result = handle_punish_unpaid_warrior(context=PunishUnpaidWarrior(warrior=warrior, faction=faction, month=3))

    assert result == WarriorLostMoraleOverUnpaidSalary(warrior=warrior, faction=faction, lost_morale=5, month=3)
    warrior.refresh_from_db()
    assert warrior.current_morale == 15


@pytest.mark.django_db
def test_handle_punish_unpaid_warrior_floors_the_loss_at_one_point():
    """
    A quarter of a levy's morale rounds to nothing for every maximum below three, and a penalty of
    zero is not a penalty.
    """
    faction = FactionFactory()
    warrior = WarriorFactory(faction=faction, current_morale=2, max_morale=2, unpaid_months=1)

    result = handle_punish_unpaid_warrior(context=PunishUnpaidWarrior(warrior=warrior, faction=faction, month=3))

    assert result.lost_morale == 1
    warrior.refresh_from_db()
    assert warrior.current_morale == 1


@pytest.mark.django_db
def test_handle_punish_unpaid_warrior_lets_him_walk_on_the_third_month():
    faction = FactionFactory()
    warrior = WarriorFactory(faction=faction, unpaid_months=3)

    result = handle_punish_unpaid_warrior(context=PunishUnpaidWarrior(warrior=warrior, faction=faction, month=3))

    assert result == WarriorWalkedOutOverUnpaidSalary(
        warrior=warrior, faction=faction, savegame=faction.savegame, month=3
    )
    warrior.refresh_from_db()
    assert warrior.faction is None


@pytest.mark.django_db
def test_handle_punish_unpaid_warrior_leaves_the_gear_of_the_man_who_walked_out_with_the_faction():
    """
    An item belongs to the faction and is only wielded by a warrior, so gear walking off the roster
    on the man who left can never be re-equipped or sold again.
    """
    faction = FactionFactory()
    weapon = ItemFactory(type=ItemTypeFactory(function=ItemType.FunctionChoices.FUNCTION_WEAPON), owner=faction)
    warrior = WarriorFactory(faction=faction, weapon=weapon, unpaid_months=3)

    handle_punish_unpaid_warrior(context=PunishUnpaidWarrior(warrior=warrior, faction=faction, month=3))

    warrior.refresh_from_db()
    weapon.refresh_from_db()
    assert (warrior.weapon, weapon.owner) == (None, faction)


@pytest.mark.django_db
def test_handle_punish_unpaid_warrior_keeps_the_leader_however_long_he_goes_unpaid():
    """
    Faction.leader is a CASCADE FK and losing the leader is what defeats a faction, so a leader
    walking out would end the game over a wage bill instead of shrinking the war band.
    """
    faction = FactionFactory()
    leader = WarriorFactory(faction=faction, current_morale=20, max_morale=20, unpaid_months=9)
    faction.leader = leader
    faction.save()

    result = handle_punish_unpaid_warrior(context=PunishUnpaidWarrior(warrior=leader, faction=faction, month=3))

    assert result == WarriorLostMoraleOverUnpaidSalary(warrior=leader, faction=faction, lost_morale=5, month=3)
    leader.refresh_from_db()
    assert leader.faction == faction


@pytest.mark.django_db
def test_handle_dismiss_warrior_takes_him_off_the_roster():
    faction = FactionFactory()
    warrior = WarriorFactory(faction=faction, monthly_salary=120)

    result = handle_dismiss_warrior(
        context=DismissWarrior(warrior=warrior, faction=faction, savegame=faction.savegame, month=3)
    )

    assert result == WarriorWasDismissed(
        warrior=warrior, faction=faction, savegame=faction.savegame, severance_pay=120, month=3
    )
    warrior.refresh_from_db()
    assert warrior.faction is None


@pytest.mark.django_db
def test_handle_dismiss_warrior_leaves_his_gear_with_the_faction():
    """
    An item belongs to the faction and is only wielded by a warrior, so gear walking off the roster
    could never be re-equipped or sold again - and that silver is the point of sending him away.
    """
    faction = FactionFactory()
    weapon = ItemFactory(type=ItemTypeFactory(function=ItemType.FunctionChoices.FUNCTION_WEAPON), owner=faction)
    warrior = WarriorFactory(faction=faction, weapon=weapon)

    handle_dismiss_warrior(context=DismissWarrior(warrior=warrior, faction=faction, savegame=faction.savegame, month=3))

    warrior.refresh_from_db()
    weapon.refresh_from_db()
    assert (warrior.weapon, weapon.owner) == (None, faction)


@pytest.mark.django_db
def test_handle_dismiss_warrior_refuses_the_leader():
    """
    Faction.leader is a CASCADE FK and losing him is what defeats a faction, so dismissing him would
    end the savegame through a roster control.
    """
    faction = FactionFactory()
    leader = WarriorFactory(faction=faction)
    faction.leader = leader
    faction.save()

    result = handle_dismiss_warrior(
        context=DismissWarrior(warrior=leader, faction=faction, savegame=faction.savegame, month=3)
    )

    assert result is None
    leader.refresh_from_db()
    assert leader.faction == faction


@pytest.mark.django_db
def test_handle_dismiss_warrior_raises_nothing_for_a_man_already_gone():
    """
    Two overlapping clicks on the one button both pass whatever the page checked, and a second event
    would bill the faction severance twice for one man.
    """
    faction = FactionFactory()
    warrior = WarriorFactory(faction=None, savegame=faction.savegame, culture=faction.culture)

    result = handle_dismiss_warrior(
        context=DismissWarrior(warrior=warrior, faction=faction, savegame=faction.savegame, month=3)
    )

    assert result is None


@pytest.mark.django_db
def test_handle_enslave_captured_warrior_carries_the_slavers_price():
    """
    The ledger books "slavery_selling_price" and the captive card advertises it, so an event carrying
    the full recruitment price named twice the silver that changes hands.
    """
    faction = FactionFactory()
    captive = WarriorFactory(faction=None, savegame=faction.savegame, culture=faction.culture, recruitment_price=97)
    faction.captured_warriors.add(captive)

    result = handle_enslave_captured_warrior(context=EnslaveCapturedWarrior(warrior=captive, faction=faction, month=3))

    assert result == WarriorWasSoldIntoSlavery(warrior=captive, selling_faction=faction, price=48, month=3)
    assert list(faction.captured_warriors.all()) == []


@pytest.mark.django_db
def test_handle_recruit_captured_warrior_gives_a_captive_his_nerve_back():
    """
    The monthly morale sweep passes captives by, so a man recruited later than the month he was taken
    in has nothing between his release and his first fight to fill him back up.
    """
    faction = FactionFactory()
    captive = WarriorFactory(
        faction=None, savegame=faction.savegame, culture=faction.culture, current_morale=0, max_morale=20
    )
    faction.captured_warriors.add(captive)

    result = handle_recruit_captured_warrior(context=RecruitCapturedWarrior(warrior=captive, faction=faction, month=3))

    assert result == [
        WarriorRecruited(warrior=captive, faction=faction, recruitment_price=0, month=3),
        WarriorMoraleReplenished(warrior=captive, faction=faction, recovered_morale=15, month=3),
    ]
    captive.refresh_from_db()
    assert captive.current_morale == 15


@pytest.mark.django_db
def test_handle_recruit_captured_warrior_reports_no_recovery_from_a_captive_at_full_morale():
    """
    A quarter off his maximum takes his current morale down with it, so a man captured with his
    spirit intact arrives full and has nothing to recover.
    """
    faction = FactionFactory()
    captive = WarriorFactory(
        faction=None, savegame=faction.savegame, culture=faction.culture, current_morale=20, max_morale=20
    )
    faction.captured_warriors.add(captive)

    result = handle_recruit_captured_warrior(context=RecruitCapturedWarrior(warrior=captive, faction=faction, month=3))

    assert result == WarriorRecruited(warrior=captive, faction=faction, recruitment_price=0, month=3)
    captive.refresh_from_db()
    assert captive.current_morale == 15


@pytest.mark.django_db
def test_handle_change_warrior_max_morale_raises_the_ceiling():
    warrior = WarriorFactory(current_morale=10, max_morale=20)

    result = handle_change_warrior_max_morale(
        context=ChangeWarriorMaxMorale(warrior=warrior, faction=warrior.faction, share=0.2, month=3)
    )

    assert result == WarriorMaxMoraleChanged(warrior=warrior, faction=warrior.faction, changed_max_morale=4, month=3)
    warrior.refresh_from_db()
    assert warrior.max_morale == 24


@pytest.mark.django_db
def test_handle_change_warrior_max_morale_lowers_the_ceiling():
    """
    Reported as the points it moved rather than the share it was asked for: the share is truncated
    against what the man has, so a levy and a veteran lose different numbers.
    """
    warrior = WarriorFactory(current_morale=20, max_morale=20)

    result = handle_change_warrior_max_morale(
        context=ChangeWarriorMaxMorale(warrior=warrior, faction=warrior.faction, share=-0.2, month=3)
    )

    assert result == WarriorMaxMoraleChanged(warrior=warrior, faction=warrior.faction, changed_max_morale=-4, month=3)
    warrior.refresh_from_db()
    assert warrior.max_morale == 16
