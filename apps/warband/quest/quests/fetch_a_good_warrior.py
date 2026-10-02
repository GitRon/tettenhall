from apps.warband.quest.quests.base import Quest, QuestOutcome
from apps.warband.warrior.services.generators.warrior.champion import ChampionWarriorGenerator
from apps.warband.warrior.services.generators.warrior.mercenary import MercenaryWarriorGenerator


class FetchAGoodWarrior(Quest):
    """
    Men sent to bring a fighter of name home to the war band.

    A champion is the success, and he is stronger than anything the pub offers. The middling outcome
    still brings a man back, an ordinary one, so it counts as a success the band's strength makes
    likelier. Either man draws a wage from the next month on, which is what this quest costs. Leans
    on strength, the thing a famous fighter asks to see before he follows anyone.
    """

    WEIGHT = 2

    TITLE = "A wandering champion has been seen at the crossroads by the old minster."
    BODY = "He is said to follow only men who can beat him, and to be seldom followed."

    MIN_MEN = 2
    MAX_MEN = 3
    LEANS_ON = "strength"
    # Three middling men
    STAT_YARDSTICK = 24

    OUTCOMES = (
        QuestOutcome(
            key="champion",
            weight=2,
            is_success=True,
            title="The champion from the crossroads came home with the war band.",
            body="He said he had let them win, and nobody was in a position to argue.",
            warrior_generator_class=ChampionWarriorGenerator,
        ),
        QuestOutcome(
            key="his_companion",
            weight=2,
            is_success=True,
            title="The champion had moved on, and his companion came home instead.",
            body="The companion said he was much the same, only cheaper.",
            warrior_generator_class=MercenaryWarriorGenerator,
        ),
        QuestOutcome(
            key="not_found",
            weight=3,
            is_success=False,
            title="The men waited at the crossroads by the old minster, and no champion came.",
            body="A man there told them he had been and gone. He would not say which way.",
        ),
    )
