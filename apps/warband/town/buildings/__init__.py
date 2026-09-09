from apps.warband.town.buildings.base import Building, BuildingEffect
from apps.warband.town.buildings.hall import Hall
from apps.warband.town.buildings.marketplace import Marketplace
from apps.warband.town.buildings.sanctuary import Sanctuary
from apps.warband.town.buildings.weaponsmith import Weaponsmith

# Keyed by the field holding the level on the town, which is also what the upgrade URL carries. Any
# building reachable from the town page has to be in here - the view upgrades nothing else.
BUILDINGS: dict[str, type[Building]] = {
    Hall.BUILDING_NAME: Hall,
    Weaponsmith.BUILDING_NAME: Weaponsmith,
    Marketplace.BUILDING_NAME: Marketplace,
    Sanctuary.BUILDING_NAME: Sanctuary,
}
