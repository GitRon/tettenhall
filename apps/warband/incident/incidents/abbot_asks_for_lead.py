from apps.warband.incident.incidents.base import Incident, IncidentOption


class AbbotAsksForLead(Incident):
    """
    The church asks for a gift, and says what not giving it would cost.

    The second question whose default costs something, alongside TributeToARival: a refusal loses a
    man from the fyrd rather than silver. The levy is clamped when the answer lands, so a player
    with an empty reserve refuses for free - the abbot has nobody left to preach to.
    """

    WEIGHT = 2

    TITLE = "The abbot of the minster asked for lead for the church roof."
    BODY = "He mentioned, in passing, how long the fyrd's mothers listen to him."

    OPTIONS = (
        IncidentOption(
            key="give",
            label="Give the lead",
            title="Lead went to the minster roof.",
            body="The abbot blessed the war band from the pulpit. He did not say which parts of it.",
            silver_change=-60,
        ),
        IncidentOption(
            key="refuse",
            label="Refuse",
            title="The abbot was refused his lead, and preached on it.",
            body="One family of the fyrd has decided the war band is godless. They were never very keen.",
            fyrd_change=-1,
        ),
    )
    DEFAULT_OPTION = "refuse"
