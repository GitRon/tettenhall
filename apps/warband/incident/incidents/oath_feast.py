import random

from apps.warband.faction.models.faction import Faction
from apps.warband.incident.incidents.base import Incident, IncidentOutcome, roster
from apps.warband.town.models.town import Town


class OathFeast(Incident):
    """
    The war band renews its oath at the mead-bench, and one man means it more than he did.

    The feast needs a hall to hold it in, so a town that has not built one never draws it. Not tied
    to a season: the game has no calendar, only a month count, and a feast that is Yule in name
    would be drawn in midsummer.

    The only raise to the morale ceiling besides [HallRelic], and the counterweight to
    [PriestDenounces] and [ChildWithHisFace] - their weighted shares sum to its own, so the ceiling
    still nets out flat.
    """

    WEIGHT = 3

    TITLE = "The war band renewed its oaths at the mead-bench, and {warrior} spoke first."
    BODY = "The words were older than the hall, and he knew all of them."

    MAX_MORALE_SHARE = 0.2

    @classmethod
    def is_possible(cls, *, faction: Faction) -> bool:
        return faction.town.hall != Town.HallChoices.HALL_NONE and bool(roster(faction=faction))

    @classmethod
    def resolve(cls, *, faction: Faction) -> IncidentOutcome:
        warrior = random.choice(roster(faction=faction))

        return IncidentOutcome(
            title=cls.TITLE.format(warrior=warrior),
            body=cls.BODY,
            max_morale_share=cls.MAX_MORALE_SHARE,
            warrior=warrior,
        )
