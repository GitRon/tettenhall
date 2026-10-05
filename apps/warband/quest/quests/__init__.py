from apps.warband.quest.quests.base import Quest
from apps.warband.quest.quests.drive_off_wolves import DriveOffWolves
from apps.warband.quest.quests.escort_thegns_daughter import EscortThegnsDaughter
from apps.warband.quest.quests.fetch_a_good_warrior import FetchAGoodWarrior
from apps.warband.quest.quests.harvest_hands import HarvestHands
from apps.warband.quest.quests.kings_summons import KingsSummons
from apps.warband.quest.quests.merchant_guard import MerchantGuard
from apps.warband.quest.quests.seek_a_good_blade import SeekAGoodBlade

QUESTS: tuple[type[Quest], ...] = (
    HarvestHands,
    MerchantGuard,
    SeekAGoodBlade,
    FetchAGoodWarrior,
    KingsSummons,
    EscortThegnsDaughter,
    DriveOffWolves,
)

# The offer and contract rows name their entry by class name, which is how they find it again
QUESTS_BY_NAME: dict[str, type[Quest]] = {quest.__name__: quest for quest in QUESTS}

# How many of each side of the catalogue a month offers. One steady-work quest always - the errand a war band
# that cannot pay its men can still send them on - and one of everything else beside it, so the
# board is a choice rather than a notice
STEADY_WORK_OFFERED = 1
ERRANDS_OFFERED = 1
