from dataclasses import dataclass

from queuebie.messages import Event

from apps.skirmish.models.skirmish_blow import SkirmishBlow
from apps.skirmish.models.skirmish_casualty import SkirmishCasualty
from apps.skirmish.models.skirmish_spoil import SkirmishSpoil
from apps.skirmish.models.skirmish_warrior_growth import SkirmishWarriorGrowth


@dataclass(kw_only=True)
class SkirmishSpoilRecorded(Event):
    spoil: SkirmishSpoil


@dataclass(kw_only=True)
class SkirmishCasualtyRecorded(Event):
    casualty: SkirmishCasualty


@dataclass(kw_only=True)
class WarriorGrowthRecorded(Event):
    growth: SkirmishWarriorGrowth


@dataclass(kw_only=True)
class SkirmishBlowRecorded(Event):
    blow: SkirmishBlow
