from apps.warband.quest.quests.base import Quest, QuestOutcome


class HarvestHands(Quest):
    """
    Steady work that is always there to be had: a thegn short of hands at the harvest.

    Pays something whatever happens, because a field is reaped either way - the draw only decides how
    much of it the men are paid for. Leans on strength, the attribute a scythe asks for.
    """

    WEIGHT = 3

    TITLE = "A thegn wants hands to bring in his barley."
    BODY = "He pays by the sheaf, and counts them himself."

    MIN_MEN = 1
    MAX_MEN = 4
    LEANS_ON = "strength"
    # Two middling men
    STAT_YARDSTICK = 16

    IS_STEADY_WORK = True

    OUTCOMES = (
        QuestOutcome(
            key="reaped",
            weight=3,
            is_success=True,
            title="The thegn's barley was brought in by the war band.",
            body="He counted the sheaves twice and paid for most of them.",
            silver_per_man=35,
        ),
        QuestOutcome(
            key="rained_off",
            weight=1,
            is_success=False,
            title="Rain stopped the thegn's harvest half-way through.",
            body="He paid for the half that was in, and blamed the half that was not.",
            silver_per_man=10,
        ),
    )
