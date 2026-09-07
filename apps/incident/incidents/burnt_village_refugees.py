from apps.incident.incidents.base import Incident


class BurntVillageRefugees(Incident):
    """
    Two levers at once: men for the fyrd, and the cost of feeding them through the winter.

    The one entry where what the player gains and what he pays for it arrive in the same line, which
    is the shape most of the catalogue in #73 should have.
    """

    WEIGHT = 3

    TITLE = "Villagers came in from a burnt settlement to the north."
    BODY = "They ask for bread and a banner to stand under. Both are given, and only one of them is cheap."

    SILVER_CHANGE = -120
    FYRD_CHANGE = 2
