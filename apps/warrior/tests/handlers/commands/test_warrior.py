from unittest import mock

import pytest

from apps.faction.handlers.commands.faction import handle_create_new_faction
from apps.faction.messages.commands.faction import CreateNewFaction
from apps.faction.tests.factories.culture import CultureFactory
from apps.faction.tests.factories.faction import FactionFactory
from apps.item.models.item_type import ItemType
from apps.item.tests.factories.item import ItemFactory
from apps.item.tests.factories.item_type import ItemTypeFactory
from apps.savegame.tests.factories.savegame import SavegameFactory
from apps.skirmish.models.warrior import Warrior
from apps.skirmish.tests.factories.warrior import WarriorFactory
from apps.warrior.handlers.commands.warrior import (
    handle_heal_injured_warrior,
    handle_punish_unpaid_warrior,
    handle_replenish_warrior_morale,
)
from apps.warrior.messages.commands.warrior import HealInjuredWarrior, PunishUnpaidWarrior, ReplenishWarriorMorale
from apps.warrior.messages.events.warrior import (
    WarriorDesertedOverUnpaidSalary,
    WarriorHealthHealed,
    WarriorLostMoraleOverUnpaidSalary,
    WarriorMoraleReplenished,
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

    with mock.patch("apps.warrior.handlers.commands.warrior.random.randrange", return_value=5):
        result = handle_heal_injured_warrior(
            context=HealInjuredWarrior(faction=warrior.faction, warrior=warrior, month=3)
        )

    assert result == WarriorHealthHealed(warrior=warrior, faction=warrior.faction, healed_points=5, month=3)
    warrior.refresh_from_db()
    assert warrior.current_health == 10


@pytest.mark.django_db
def test_handle_heal_injured_warrior_caps_healing_at_the_maximum():
    warrior = WarriorFactory(current_health=18, max_health=20)

    with mock.patch("apps.warrior.handlers.commands.warrior.random.randrange", return_value=5):
        result = handle_heal_injured_warrior(
            context=HealInjuredWarrior(faction=warrior.faction, warrior=warrior, month=3)
        )

    assert result == WarriorHealthHealed(warrior=warrior, faction=warrior.faction, healed_points=2, month=3)
    warrior.refresh_from_db()
    assert warrior.current_health == 20


@pytest.mark.django_db
def test_handle_heal_injured_warrior_at_full_health():
    warrior = WarriorFactory(current_health=20, max_health=20)

    with mock.patch("apps.warrior.handlers.commands.warrior.random.randrange", return_value=5):
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

    with mock.patch("apps.warrior.handlers.commands.warrior.random.randrange", return_value=8) as mocked_randrange:
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

    with mock.patch("apps.warrior.handlers.commands.warrior.random.randrange", return_value=1) as mocked_randrange:
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

    with mock.patch("apps.warrior.handlers.commands.warrior.random.randrange", return_value=1) as mocked_randrange:
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

    with mock.patch("apps.warrior.handlers.commands.warrior.random.randrange", return_value=8) as mocked_randrange:
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

    with mock.patch("apps.warrior.handlers.commands.warrior.random.randrange", return_value=4):
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

    assert result == WarriorDesertedOverUnpaidSalary(warrior=warrior, faction=faction, month=3)
    warrior.refresh_from_db()
    assert warrior.faction is None


@pytest.mark.django_db
def test_handle_punish_unpaid_warrior_leaves_a_deserters_gear_with_the_faction():
    """
    An item belongs to the faction and is only wielded by a warrior, so gear walking off the roster
    on a deserter can never be re-equipped or sold again.
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
    deserting would end the game over a wage bill instead of shrinking the war band.
    """
    faction = FactionFactory()
    leader = WarriorFactory(faction=faction, current_morale=20, max_morale=20, unpaid_months=9)
    faction.leader = leader
    faction.save()

    result = handle_punish_unpaid_warrior(context=PunishUnpaidWarrior(warrior=leader, faction=faction, month=3))

    assert result == WarriorLostMoraleOverUnpaidSalary(warrior=leader, faction=faction, lost_morale=5, month=3)
    leader.refresh_from_db()
    assert leader.faction == faction
