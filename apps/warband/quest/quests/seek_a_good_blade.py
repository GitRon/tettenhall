from apps.warband.item.models.item_type import ItemType
from apps.warband.item.services.generators.item.mercenary import MercenaryItemGenerator
from apps.warband.quest.quests.base import Quest, QuestOutcome


class SeekAGoodBlade(Quest):
    """
    Men sent after a blade of renown, the one way to arm the band better than the town's shelf does.

    The quality bonus sits above the best weaponsmith's, so what comes home is gear no amount of
    building buys. More often nothing comes home at all, which is what keeps it from being a shop with
    a month's delay. Leans on dexterity: the work is finding the thing, not carrying it.
    """

    WEIGHT = 2

    TITLE = "A sword is said to lie with a drowned king in the fens."
    BODY = "Several people have said so. None of them has been to look."

    MIN_MEN = 2
    MAX_MEN = 3
    LEANS_ON = "dexterity"
    # Two and a half middling men
    STAT_YARDSTICK = 20

    OUTCOMES = (
        QuestOutcome(
            key="found",
            weight=2,
            is_success=True,
            title="The men came back from the fens with the drowned king's sword.",
            body="The king was not with it, which was thought to be for the best.",
            item_function=ItemType.FunctionChoices.FUNCTION_WEAPON,
            item_generator_class=MercenaryItemGenerator,
            # One above the best weaponsmith in the game
            item_quality_bonus=4,
        ),
        QuestOutcome(
            key="mud",
            weight=3,
            is_success=False,
            title="The men searched the fens for the drowned king's sword and found mud.",
            body="They described it at some length.",
        ),
    )
