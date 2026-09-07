from apps.incident.incidents.base import Incident


class AlefeastOverruns(Incident):
    """
    The war band drank for three days longer than it was fed for.
    """

    WEIGHT = 3

    TITLE = "The war band's ale feast ran three days over."
    BODY = "The brewer's account is itemised. Two of the items are furniture."

    SILVER_CHANGE = -90
