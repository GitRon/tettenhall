import pytest

from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.skirmish.raids.kinds import BurnTheVillage, LiftTheHerds, StormTheBurh
from apps.warband.town.buildings.fortification import NPC_STARTING_FORTIFICATION_LEVEL, Palisade


def test_get_label_reads_the_stored_choice():
    assert LiftTheHerds.get_label() == "Lift the herds"


@pytest.mark.django_db
def test_get_fortification_strength_is_the_towns_wall_on_the_burh():
    faction = FactionFactory(town__fortification=NPC_STARTING_FORTIFICATION_LEVEL)

    assert StormTheBurh.get_fortification_strength(town=faction.town) == Palisade.FORTIFICATION_STRENGTH


@pytest.mark.django_db
def test_get_fortification_strength_is_an_open_field_out_in_the_shire():
    faction = FactionFactory(town__fortification=NPC_STARTING_FORTIFICATION_LEVEL)

    assert LiftTheHerds.get_fortification_strength(town=faction.town) == 0


def test_get_purse_taken_takes_its_share():
    assert LiftTheHerds.get_purse_taken(balance=500) == 100


def test_get_purse_taken_stops_at_the_cap():
    assert LiftTheHerds.get_purse_taken(balance=5000) == LiftTheHerds.PURSE_CAP


def test_get_purse_taken_finds_nothing_in_an_empty_purse():
    assert LiftTheHerds.get_purse_taken(balance=0) == 0


def test_get_purse_taken_finds_nothing_in_a_purse_in_debt():
    assert LiftTheHerds.get_purse_taken(balance=-40) == 0


def test_get_purse_taken_is_nothing_for_a_raid_that_takes_no_silver():
    assert BurnTheVillage.get_purse_taken(balance=500) == 0


def test_get_fyrd_names_burned_strikes_its_names():
    assert BurnTheVillage.get_fyrd_names_burned(fyrd_reserve=10) == BurnTheVillage.FYRD_NAMES_BURNED


def test_get_fyrd_names_burned_never_strikes_more_than_there_are():
    assert BurnTheVillage.get_fyrd_names_burned(fyrd_reserve=1) == 1


def test_get_skirmish_name_is_the_attack_on_the_town():
    faction = FactionFactory.build(name="Bernicia")

    assert StormTheBurh.get_skirmish_name(target=faction) == "Attack on Bernicia"


def test_get_effects_names_the_share_of_the_purse():
    assert LiftTheHerds.get_effects() == (
        f"{LiftTheHerds.LOCALS_TURNOUT} herdsmen turn out to defend it",
        f"Drives off 20% of their silver, at most {LiftTheHerds.PURSE_CAP}",
        "Leaves the town standing",
    )


def test_get_effects_names_the_fyrd_burned():
    assert BurnTheVillage.get_effects() == (
        f"{BurnTheVillage.LOCALS_TURNOUT} villagers turn out to defend it",
        f"Strikes {BurnTheVillage.FYRD_NAMES_BURNED} names off their fyrd",
        "Leaves the town standing",
    )


def test_get_effects_says_the_burh_opens_the_town():
    assert StormTheBurh.get_effects() == (
        f"{StormTheBurh.LOCALS_TURNOUT} men of the fyrd turn out to defend it",
        "Opens the town to be ridden into",
    )
