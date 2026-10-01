from queuebie import message_registry
from queuebie.messages import Command

from apps.warband.month.messages.commands.month import CreatePlayerMonthLog
from apps.warband.month.models.player_month_log import PlayerMonthLog
from apps.warband.quest.messages.events.quest_contract import QuestContractLapsed, QuestContractReturned
from apps.warband.quest.quests import QUESTS_BY_NAME


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
