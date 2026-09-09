from apps.warband.incident.incidents.base import Incident


class PloughHoard(Incident):
    """
    Old coin turned up by a plough.

    The one straight windfall in the catalogue, and the reason the silver entries are weighted to net
    out against it: #45 gave insolvency teeth and #3 is about to make silver contested, so a pool
    that pays out on average flattens both.
    """

    WEIGHT = 4

    TITLE = "A ploughman on the west field turned up a hoard of old coin."
    BODY = (
        "He kept back a handful, by the reckoning of the man sent to count it, "
        "and the man sent to count it kept back two."
    )

    # Two thirds of a levy's monthly wage. Enough to be worth reading, not enough to be a plan
    SILVER_CHANGE = 150
