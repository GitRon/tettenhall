from apps.incident.incidents.base import Incident


class HallRoofFallsIn(Incident):
    """
    The hall needs a roof again, at the going rate for thatchers.
    """

    WEIGHT = 4

    TITLE = "The hall roof came down in the night."
    BODY = (
        "Nobody was beneath it. The thatcher who swore it would hold another winter was, by then, three villages away."
    )

    # The dearest entry in the catalogue, and the counterweight to the hoard
    SILVER_CHANGE = -180
