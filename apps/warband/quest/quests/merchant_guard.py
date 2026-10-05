from apps.warband.quest.quests.base import Quest, QuestOutcome


class MerchantGuard(Quest):
    """
    The other steady work: walking a merchant's pack-train to the next market.

    Better paid than the harvest and less certain of it. Leans on dexterity, the attribute a man
    watching a treeline needs.
    """

    WEIGHT = 3

    TITLE = "A merchant wants an escort to the market at Lundenwic."
    BODY = "He says the road is quite safe, and wants armed men on it."

    MIN_MEN = 1
    MAX_MEN = 3
    LEANS_ON = "dexterity"
    # Two middling men
    STAT_YARDSTICK = 16

    IS_STEADY_WORK = True

    OUTCOMES = (
        QuestOutcome(
            key="delivered",
            weight=3,
            is_success=True,
            title="The merchant reached Lundenwic with every bale he set out with.",
            body="He paid the escort, and said he had never been in any danger.",
            silver_per_man=45,
        ),
        QuestOutcome(
            key="market_over",
            weight=1,
            is_success=False,
            title="The merchant reached Lundenwic and found the market already over.",
            body="He paid the escort in the cloth nobody had bought.",
            silver_per_man=5,
        ),
    )
