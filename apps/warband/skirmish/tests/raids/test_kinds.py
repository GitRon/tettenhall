from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.skirmish.raids.kinds import BurnTheVillage, LiftTheHerds


def test_lift_the_herds_get_skirmish_name():
    faction = FactionFactory.build(name="Bernicia")

    assert LiftTheHerds.get_skirmish_name(target=faction) == "Raid on the herds of Bernicia"


def test_burn_the_village_get_skirmish_name():
    faction = FactionFactory.build(name="Bernicia")

    assert BurnTheVillage.get_skirmish_name(target=faction) == "Burning of the village of Bernicia"
