# Django finds a model through the app it is declared in, and every model of this app lives one level
# further down in a topic package. Re-exporting them here is what puts them in the app registry, so a
# topic package that owns a model has to be listed below or its table is never created.
from apps.warband.faction.models import Culture, Faction
from apps.warband.finance.models import Transaction
from apps.warband.item.models import Item, ItemType
from apps.warband.month.models import PlayerMonthLog
from apps.warband.quest.models import Quest, QuestContract, QuestName
from apps.warband.savegame.models.savegame import Savegame
from apps.warband.skirmish.models import (
    BattleHistory,
    Skirmish,
    SkirmishBlow,
    SkirmishCasualty,
    SkirmishSpoil,
    SkirmishWarriorGrowth,
    Warrior,
)
from apps.warband.town.models import Town
from apps.warband.training.models import Training

__all__ = [
    "BattleHistory",
    "Culture",
    "Faction",
    "Item",
    "ItemType",
    "PlayerMonthLog",
    "Quest",
    "QuestContract",
    "QuestName",
    "Savegame",
    "Skirmish",
    "SkirmishBlow",
    "SkirmishCasualty",
    "SkirmishSpoil",
    "SkirmishWarriorGrowth",
    "Town",
    "Training",
    "Transaction",
    "Warrior",
]
