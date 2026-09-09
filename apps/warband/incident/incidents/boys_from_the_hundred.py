from apps.warband.incident.incidents.base import Incident


class BoysFromTheHundred(Incident):
    """
    One more name in the fyrd, for nothing.
    """

    WEIGHT = 2

    TITLE = "Boys from the hundred came asking after the war band."
    BODY = "One of them can already draw a bow. He is the one who talks least about it."

    FYRD_CHANGE = 1
