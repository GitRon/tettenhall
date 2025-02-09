from dataclasses import dataclass

from queuebie.messages import Command

from apps.savegame.models.savegame import Savegame


@dataclass(kw_only=True)
class PrepareMonth(Command):
    savegame: Savegame
