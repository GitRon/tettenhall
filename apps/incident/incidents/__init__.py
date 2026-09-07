from apps.incident.incidents.alefeast_overruns import AlefeastOverruns
from apps.incident.incidents.base import Incident, IncidentOutcome
from apps.incident.incidents.boys_from_the_hundred import BoysFromTheHundred
from apps.incident.incidents.burnt_village_refugees import BurntVillageRefugees
from apps.incident.incidents.devil_at_the_ford import DevilAtTheFord
from apps.incident.incidents.fever_in_the_villages import FeverInTheVillages
from apps.incident.incidents.hall_relic import HallRelic
from apps.incident.incidents.hall_roof_falls_in import HallRoofFallsIn
from apps.incident.incidents.moor_lost_gear import MoorLostGear
from apps.incident.incidents.plough_hoard import PloughHoard
from apps.incident.incidents.toll_on_the_old_road import TollOnTheOldRoad

# The pool one month is drawn from. A tuple rather than a scan of the package, so an entry is in the
# game because somebody put it here - the same thing BUILDINGS is to a town.
INCIDENTS: tuple[type[Incident], ...] = (
    PloughHoard,
    HallRoofFallsIn,
    TollOnTheOldRoad,
    AlefeastOverruns,
    BurntVillageRefugees,
    FeverInTheVillages,
    HallRelic,
    DevilAtTheFord,
    BoysFromTheHundred,
    MoorLostGear,
)

# The odds of a month in which nothing happens, weighted against the pool rather than left as the
# absence of an incident. The one number here meant to be tuned directly: without it, the chance of
# a quiet month would change silently every time an entry is added, and it is also what makes an
# empty candidate set unremarkable - a month with nothing possible is a quiet month like any other.
#
# Against the 30 points the pool carries it puts an incident at 30 in 90, so something happens about
# one month in three - which is the dosage the register needs. The tone works because most entries
# are genuinely dry, and it stops working if the chronicle speaks every month.
QUIET_MONTH_WEIGHT = 60
