from apps.warband.incident.incidents.base import Incident, IncidentOption


class BurntVillageRefugees(Incident):
    """
    Men for the fyrd, and the cost of feeding them through the winter - if the player takes them.

    The question whose default only misses a gain: turning the villagers away changes nothing, and
    the levy that did not join is the price. Paired with TributeToARival, whose default costs
    something, so both shapes of a question are in the catalogue.
    """

    WEIGHT = 3

    TITLE = "Villagers came in from a burnt settlement to the north."
    BODY = "They ask for bread and a banner to stand under. Both can be given, and only one of them is cheap."

    OPTIONS = (
        IncidentOption(
            key="take_in",
            label="Take them in",
            title="The villagers from the north were taken in.",
            body="Bread and a banner were both given, and only one of them was cheap.",
            silver_change=-120,
            fyrd_change=2,
        ),
        IncidentOption(
            key="turn_away",
            label="Turn them away",
            title="The villagers from the north were sent on.",
            body="They went south to try another hall's door.",
        ),
    )
    DEFAULT_OPTION = "turn_away"
