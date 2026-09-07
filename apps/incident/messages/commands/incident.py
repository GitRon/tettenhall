from dataclasses import dataclass

from queuebie.messages import Command

from apps.faction.models.faction import Faction


@dataclass(kw_only=True)
class ChooseIncident(Command):
    """
    Roll for what the world does to this faction this month.

    A command rather than the event handler doing it, because choosing needs to ask questions -
    does the treasury cover the repair, is there a spare blade to lose - and strict mode blocks
    every database read inside an event handler.
    """

    faction: Faction
    month: int
