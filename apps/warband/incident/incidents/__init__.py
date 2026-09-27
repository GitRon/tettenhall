from apps.warband.incident.incidents.abbot_asks_for_lead import AbbotAsksForLead
from apps.warband.incident.incidents.alefeast_overruns import AlefeastOverruns
from apps.warband.incident.incidents.base import Incident, IncidentOutcome
from apps.warband.incident.incidents.boys_from_the_hundred import BoysFromTheHundred
from apps.warband.incident.incidents.burnt_village_refugees import BurntVillageRefugees
from apps.warband.incident.incidents.child_with_his_face import ChildWithHisFace
from apps.warband.incident.incidents.devil_at_the_ford import DevilAtTheFord
from apps.warband.incident.incidents.elf_shot_herd import ElfShotHerd
from apps.warband.incident.incidents.fever_in_the_villages import FeverInTheVillages
from apps.warband.incident.incidents.frisian_trader_wants_mail import FrisianTraderWantsMail
from apps.warband.incident.incidents.hall_relic import HallRelic
from apps.warband.incident.incidents.hall_roof_falls_in import HallRoofFallsIn
from apps.warband.incident.incidents.moor_lost_gear import MoorLostGear
from apps.warband.incident.incidents.oath_feast import OathFeast
from apps.warband.incident.incidents.plough_hoard import PloughHoard
from apps.warband.incident.incidents.priest_denounces import PriestDenounces
from apps.warband.incident.incidents.thegn_buys_out_his_sons import ThegnBuysOutHisSons
from apps.warband.incident.incidents.toll_on_the_old_road import TollOnTheOldRoad
from apps.warband.incident.incidents.tribute_to_a_rival import TributeToARival
from apps.warband.incident.incidents.wergild_claimed import WergildClaimed

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
    WergildClaimed,
    ElfShotHerd,
    TributeToARival,
    OathFeast,
    PriestDenounces,
    ChildWithHisFace,
    ThegnBuysOutHisSons,
    AbbotAsksForLead,
    FrisianTraderWantsMail,
)

# How a pending question finds its entry again when it is answered. Keyed by class name, which is what
# "PendingIncident.incident" stores
INCIDENTS_BY_NAME: dict[str, type[Incident]] = {incident.__name__: incident for incident in INCIDENTS}

# The odds of a month in which nothing happens, weighted against the pool rather than left as the
# absence of an incident. The one number here meant to be tuned directly: without it, the chance of
# a quiet month would change silently every time an entry is added, and it is also what makes an
# empty candidate set unremarkable - a month with nothing possible is a quiet month like any other.
#
# Against the 51 points the pool carries across a year it puts an incident at 51 in 141, so something
# happens about one month in three - which is the dosage the register needs. The Yule months carry
# more, 66 points, because the oath feast is drawn only then: an incident about one month in two and
# a half there, still less often than a quiet one. The tone works because most entries
# are genuinely dry, and it stops working if the chronicle speaks every month.
QUIET_MONTH_WEIGHT = 90
