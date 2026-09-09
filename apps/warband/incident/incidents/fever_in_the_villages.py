from apps.warband.faction.models.faction import Faction
from apps.warband.incident.incidents.base import Incident, IncidentOutcome


class FeverInTheVillages(Incident):
    """
    The fyrd is thinner than it was, and nobody chose it.

    Reported plainly: the register's joke is vanity and superstition, never the dying. What it costs
    the player is the brake on his own growth, which is the lever the reserve is.
    """

    WEIGHT = 3

    TITLE = "A fever went through the villages of the fyrd."
    BODY = "It took the old and the very young. Fewer names will answer a call this year."

    FYRD_CHANGE = -2

    @classmethod
    def is_possible(cls, *, faction: Faction) -> bool:
        return faction.fyrd_reserve > 0

    @classmethod
    def resolve(cls, *, faction: Faction) -> IncidentOutcome:
        # Clamped to what the reserve actually holds, so the command is never asked for men who are
        # not there. "reduce_fyrd_reserve" floors at zero as well, but a lie on the way in would
        # reach the log line
        return IncidentOutcome(
            title=cls.TITLE,
            body=cls.BODY,
            fyrd_change=-min(-cls.FYRD_CHANGE, faction.fyrd_reserve),
        )
