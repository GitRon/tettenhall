from dataclasses import dataclass

from queuebie.messages import Command


@dataclass(kw_only=True)
class CreateNewSavegame(Command):
    faction_name: str
    town_name: str
    faction_culture_id: int
    created_by_id: int
