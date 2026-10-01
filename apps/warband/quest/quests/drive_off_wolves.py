from apps.warband.quest.quests.base import Quest, QuestOutcome


class DriveOffWolves(Quest):
    """
    Driving the wolves off the high pastures: the herdsmen pay a little and talk about it a lot.

    Silver and renown together, and less of each than the errands that pay one of them. Leans on
    strength. Nobody is hurt either way: an injury never mends, and a quest is not a fight.
    """

    WEIGHT = 3

    TITLE = "Wolves have been taking lambs on the high pastures."
    BODY = "The herdsmen have counted the lambs. The wolves have not been counted."

    MIN_MEN = 2
    MAX_MEN = 4
    LEANS_ON = "strength"
    # Three middling men
    STAT_YARDSTICK = 24

    OUTCOMES = (
        QuestOutcome(
            key="driven_off",
            weight=3,
            is_success=True,
            title="The wolves were driven off the high pastures by the war band.",
            body="The herdsmen paid what they had and told the story to anyone who would stop.",
            silver_per_man=15,
            renown_per_man=3,
        ),
        QuestOutcome(
            key="no_wolves",
            weight=2,
            is_success=False,
            title="The men watched the high pastures for a month and saw no wolves.",
            body="Two more lambs were gone by the time they came down.",
        ),
    )
