from apps.warband.quest.quests.base import Quest, QuestOutcome


class EscortThegnsDaughter(Quest):
    """
    Seeing a thegn's daughter safe to the minster: silver and a little standing for a long walk.

    Leans on health rather than on a fighting attribute, because the danger on the road is the road -
    a band that arrives is a band that did not fall behind.
    """

    WEIGHT = 3

    TITLE = "A thegn wants his daughter taken to the minster at Lichfield."
    BODY = "She has said she does not wish to go, at length and to everyone."

    MIN_MEN = 2
    MAX_MEN = 3
    LEANS_ON = "max_health"
    # Two and a half middling men
    STAT_YARDSTICK = 90

    OUTCOMES = (
        QuestOutcome(
            key="delivered",
            weight=3,
            is_success=True,
            title="The thegn's daughter reached the minster at Lichfield.",
            body="The abbess thanked the men, and then thanked them again for leaving.",
            silver_per_man=30,
            renown_per_man=3,
        ),
        QuestOutcome(
            key="turned_back",
            weight=1,
            is_success=False,
            title="The thegn's daughter was brought back home before she reached the minster.",
            body="The men said she had been unwell. She said nothing, and looked well.",
        ),
    )
