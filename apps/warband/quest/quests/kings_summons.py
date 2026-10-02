from apps.warband.quest.quests.base import Quest, QuestOutcome


class KingsSummons(Quest):
    """
    Carrying the king's summons to the hundred: an errand that pays in standing and nothing else.

    The safe way to earn renown, so it earns less than a fight does - a level-one man put down in a
    fight is worth ten (`Warrior.RENOWN_PER_LEVEL_OF_THE_FALLEN`), this is worth six. Leans on the
    morale ceiling, because the work is standing in front of a hall full of thegns and being heard.
    """

    WEIGHT = 3

    TITLE = "The king's summons wants carrying to the hundred-moot."
    BODY = "The last man to carry it is still explaining why he was late."

    MIN_MEN = 1
    MAX_MEN = 2
    LEANS_ON = "max_morale"
    # One and a half middling men
    STAT_YARDSTICK = 12

    OUTCOMES = (
        QuestOutcome(
            key="heard",
            weight=3,
            is_success=True,
            title="The king's summons was read out at the hundred-moot by the war band's men.",
            body="It was heard in silence, which they took as respect.",
            renown_per_man=6,
        ),
        QuestOutcome(
            key="shouted_down",
            weight=1,
            is_success=False,
            title="The king's summons was read out at the hundred-moot and shouted down.",
            body="The men were thanked for bringing it, by the man who had shouted loudest.",
        ),
    )
