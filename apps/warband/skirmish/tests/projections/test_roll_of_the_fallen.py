import pytest

from apps.warband.skirmish.models import BattleHistory, SkirmishCasualty
from apps.warband.skirmish.projections.roll_of_the_fallen import FallenWarrior, RollOfTheFallen
from apps.warband.skirmish.tests.factories.battle_history import BattleHistoryFactory
from apps.warband.skirmish.tests.factories.skirmish import SkirmishFactory
from apps.warband.skirmish.tests.factories.skirmish_casualty import SkirmishCasualtyFactory
from apps.warband.skirmish.tests.factories.warrior import WarriorFactory


@pytest.mark.django_db
def test_for_faction_names_the_fight_the_killer_and_the_death_line():
    skirmish = SkirmishFactory()
    killer = WarriorFactory(faction=skirmish.defending_faction)
    casualty = SkirmishCasualtyFactory(skirmish=skirmish, killed_by=killer, fell_as_a_leader=True)
    skirmish.attacking_warriors.add(casualty.warrior)
    BattleHistoryFactory(
        skirmish=skirmish,
        kind=BattleHistory.KindChoices.KIND_WARRIOR_KILLED,
        warrior=casualty.warrior,
        saga="Cuthred falls, and the ravens have him.",
    )

    result = RollOfTheFallen.for_faction(faction=skirmish.attacking_faction)

    assert result.fallen_warriors == [
        FallenWarrior(
            warrior=casualty.warrior,
            skirmish=skirmish,
            killed_by=killer,
            fell_as_a_leader=True,
            death_saga="Cuthred falls, and the ravens have him.",
            fights_stood_in=1,
        )
    ]


@pytest.mark.django_db
def test_for_faction_keeps_a_death_recorded_before_the_killer_and_the_line_were():
    casualty = SkirmishCasualtyFactory()

    result = RollOfTheFallen.for_faction(faction=casualty.warrior.faction)

    assert (result.fallen_warriors[0].killed_by, result.fallen_warriors[0].death_saga) == (None, "")


@pytest.mark.django_db
def test_for_faction_puts_the_last_man_to_fall_first_and_counts_his_fights():
    first = SkirmishCasualtyFactory()
    faction = first.warrior.faction
    later_skirmish = SkirmishFactory(attacking_faction=faction)
    last = SkirmishCasualtyFactory(skirmish=later_skirmish)
    # He stood in both fights, attacking in one and holding the line in another
    first.skirmish.attacking_warriors.add(last.warrior)
    SkirmishFactory(attacking_faction=faction).defending_warriors.add(last.warrior)

    result = RollOfTheFallen.for_faction(faction=faction)

    assert [(fallen.warrior, fallen.fights_stood_in) for fallen in result.fallen_warriors] == [
        (last.warrior, 2),
        (first.warrior, 0),
    ]


@pytest.mark.django_db
def test_for_faction_leaves_out_the_living_and_another_factions_dead():
    casualty = SkirmishCasualtyFactory()
    SkirmishCasualtyFactory(skirmish=casualty.skirmish, fate=SkirmishCasualty.FateChoices.FATE_CAPTURED)
    SkirmishCasualtyFactory(skirmish=casualty.skirmish, warrior__faction=casualty.skirmish.defending_faction)

    result = RollOfTheFallen.for_faction(faction=casualty.warrior.faction)

    assert [fallen.warrior for fallen in result.fallen_warriors] == [casualty.warrior]


@pytest.mark.django_db
def test_killer_side_is_the_defender_when_he_fell_attacking():
    casualty = SkirmishCasualtyFactory()

    fallen = RollOfTheFallen.for_faction(faction=casualty.skirmish.attacking_faction).fallen_warriors[0]

    assert fallen.killer_side == casualty.skirmish.defending_faction


@pytest.mark.django_db
def test_killer_side_is_the_attacker_when_he_fell_defending():
    """
    Read off the fight, not off the killer: a killer captured since serves whoever took him.
    """
    skirmish = SkirmishFactory()
    killer = WarriorFactory(
        faction=None, savegame=skirmish.attacking_faction.savegame, culture=skirmish.attacking_faction.culture
    )
    SkirmishCasualtyFactory(skirmish=skirmish, warrior__faction=skirmish.defending_faction, killed_by=killer)

    fallen = RollOfTheFallen.for_faction(faction=skirmish.defending_faction).fallen_warriors[0]

    assert fallen.killer_side == skirmish.attacking_faction
