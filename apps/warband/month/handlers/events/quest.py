from queuebie import message_registry
from queuebie.messages import Command

from apps.warband.item.models.item_type import ItemType
from apps.warband.month.messages.commands.month import CreatePlayerMonthLog
from apps.warband.month.models.player_month_log import PlayerMonthLog
from apps.warband.quest.messages.events.quest_contract import QuestContractLapsed, QuestContractReturned
from apps.warband.quest.quests import QUESTS_BY_NAME


def _get_brought_home_tags(*, context: QuestContractReturned) -> list[str]:
    """
    What the men brought home, one tag per kind of reward, in the order the levers are written.

    Silver is the purse total, counted over the men who came home rather than the men sent - the
    same sum the ledger books. Renown is what each of them earned. A lever the outcome does not pull
    has no tag, so an errand that paid nothing says nothing under its line.
    """
    outcome = context.outcome
    tags = []

    if outcome.silver_per_man:
        tags.append(f"{outcome.silver_per_man * len(context.warriors)} silver")
    if outcome.renown_per_man:
        tags.append(f"{outcome.renown_per_man} renown a man")
    if outcome.item_function is not None:
        # The function's name alone, as the board tags it before the men set out
        tags.append(ItemType.FunctionChoices(outcome.item_function).label)
    if outcome.warrior_generator_class is not None:
        tags.append("A man joins")

    return tags


@message_registry.register_event(event=QuestContractReturned)
def handle_write_returned_quest_to_month_log(*, context: QuestContractReturned) -> Command:
    """
    The one reaction every returning quest has: the player reads what it brought home.

    Dated to the month the men came home in, which is the month the log is cleared for, so the line
    is read on the page the month turn lands on.
    """
    return CreatePlayerMonthLog(
        title=context.outcome.title,
        body=context.outcome.body,
        tags=_get_brought_home_tags(context=context),
        kind=PlayerMonthLog.KindChoices.KIND_QUEST_RETURNED,
        month=context.month,
        faction=context.faction,
    )


@message_registry.register_event(event=QuestContractLapsed)
def handle_write_lapsed_quest_to_month_log(*, context: QuestContractLapsed) -> Command:
    quest = QUESTS_BY_NAME[context.quest_contract.quest]

    return CreatePlayerMonthLog(
        title=quest.LAPSED_TITLE,
        body=quest.LAPSED_BODY,
        kind=PlayerMonthLog.KindChoices.KIND_QUEST_RETURNED,
        month=context.month,
        faction=context.faction,
    )
