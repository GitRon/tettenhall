from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.skirmish.tests.factories.warrior import WarriorFactory
from apps.warband.warrior.handlers.events.warrior import handle_raised_ceiling_earns_a_nickname
from apps.warband.warrior.messages.commands.warrior import AwardEarnedNickname
from apps.warband.warrior.messages.events.warrior import WarriorMaxMoraleChanged


def test_handle_raised_ceiling_earns_a_nickname_asks_after_a_relic():
    faction = FactionFactory.build()
    warrior = WarriorFactory.build(faction=faction)

    result = handle_raised_ceiling_earns_a_nickname(
        context=WarriorMaxMoraleChanged(warrior=warrior, faction=faction, changed_max_morale=4, month=3)
    )

    assert result == AwardEarnedNickname(warrior=warrior, month=3)


def test_handle_raised_ceiling_earns_a_nickname_stays_out_of_a_cut():
    """
    The Devil at the ford, carrying the same share the relic adds. A man whose nerve has just been taken
    off him may be at the bottom of what his kind rolls, and naming him for that is the rename downward
    the whole story exists to stop.
    """
    faction = FactionFactory.build()
    warrior = WarriorFactory.build(faction=faction)

    result = handle_raised_ceiling_earns_a_nickname(
        context=WarriorMaxMoraleChanged(warrior=warrior, faction=faction, changed_max_morale=-4, month=3)
    )

    assert result is None


def test_handle_raised_ceiling_earns_a_nickname_stays_out_of_a_cut_that_took_nothing():
    """
    A cut is truncated against what the man has, so a levy with four morale loses none of it - and a
    ceiling that did not move is not a gain.
    """
    faction = FactionFactory.build()
    warrior = WarriorFactory.build(faction=faction)

    result = handle_raised_ceiling_earns_a_nickname(
        context=WarriorMaxMoraleChanged(warrior=warrior, faction=faction, changed_max_morale=0, month=3)
    )

    assert result is None
