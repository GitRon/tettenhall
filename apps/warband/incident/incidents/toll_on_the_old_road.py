from apps.warband.incident.incidents.base import Incident


class TollOnTheOldRoad(Incident):
    """
    A month in which the traders paid to pass.
    """

    WEIGHT = 3

    TITLE = "Traders paid to use the old road this month."
    BODY = "They asked what the toll bought them. They were told: the road."

    SILVER_CHANGE = 80
