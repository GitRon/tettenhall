from dataclasses import dataclass

from queuebie.messages import Command

from apps.faction.models.faction import Faction


@dataclass(kw_only=True)
class DraftWarriorFromFyrd(Command):
    faction: Faction
