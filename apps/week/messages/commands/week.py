from dataclasses import dataclass

from apps.core.event_loop.messages import Command
from apps.savegame.models.savegame import Savegame


class PrepareWeek(Command):
    @dataclass(kw_only=True)
    class Context:
        savegame: Savegame
