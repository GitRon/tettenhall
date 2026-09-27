from apps.warband.faction.models.faction import Faction
from apps.warband.incident.incidents.base import Incident, IncidentOption


class ThegnBuysOutHisSons(Incident):
    """
    Silver for men, the trade BurntVillageRefugees offers the other way round.

    Refusing changes nothing, so the question is only whether a few coins are worth a name off the
    fyrd roll. Only asked while there is a name on it to strike.
    """

    WEIGHT = 2

    TITLE = "A thegn offered silver to keep his sons out of the fyrd."
    BODY = "He called it a gift, and asked that it not be called anything."

    OPTIONS = (
        IncidentOption(
            key="accept",
            label="Take the silver",
            title="The thegn's silver was taken, and his sons stayed home.",
            body="Their names were struck from the fyrd roll. His was written down somewhere else.",
            silver_change=80,
            fyrd_change=-1,
        ),
        IncidentOption(
            key="refuse",
            label="Refuse",
            title="The thegn's gift was refused, and his sons stayed on the fyrd roll.",
            body="He took the silver home. The sons, it is said, would rather he had not.",
        ),
    )
    DEFAULT_OPTION = "refuse"

    @classmethod
    def is_possible(cls, *, faction: Faction) -> bool:
        return faction.fyrd_reserve > 0
