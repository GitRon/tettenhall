from dataclasses import dataclass

from apps.core.event_loop.messages import Command
from apps.faction.models.faction import Faction
from apps.skirmish.models.skirmish import Skirmish
from apps.skirmish.models.warrior import Warrior


class WarriorDropsLoot(Command):
    @dataclass(kw_only=True)
    class Context:
        skirmish: Skirmish
        warrior: Warrior
        new_owner: Faction
