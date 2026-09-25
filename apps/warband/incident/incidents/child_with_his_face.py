import random

from apps.warband.faction.models.faction import Faction
from apps.warband.incident.incidents.base import Incident, IncidentOutcome, roster


class ChildWithHisFace(Incident):
    """
    Gossip, which the register allows as a joke, at the cost of one man's standing in the hall.

    Dry register: the joke is the hall's silence, never the child. The same share as
    [DevilAtTheFord], because being talked about behind one's back wears a man down as surely as a
    fright does - and weighted lower, since a village can only have so many of these.
    """

    WEIGHT = 2

    TITLE = "A child in the village has {warrior}'s face, and another man's name."
    BODY = "The hall has noticed. Nobody says anything."

    MAX_MORALE_SHARE = -0.2

    @classmethod
    def is_possible(cls, *, faction: Faction) -> bool:
        return bool(roster(faction=faction))

    @classmethod
    def resolve(cls, *, faction: Faction) -> IncidentOutcome:
        warrior = random.choice(roster(faction=faction))

        return IncidentOutcome(
            title=cls.TITLE.format(warrior=warrior),
            body=cls.BODY,
            max_morale_share=cls.MAX_MORALE_SHARE,
            warrior=warrior,
        )
