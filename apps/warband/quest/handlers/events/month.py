from queuebie import message_registry
from queuebie.messages import Command

from apps.warband.month.messages.events.month import PlayerMonthPrepared
from apps.warband.quest.messages.commands.quest import OfferQuests
from apps.warband.quest.messages.commands.quest_contract import BringQuestContractsHome


# The player's alone, like the incidents: a rival has no board to read an offer on
@message_registry.register_event(event=PlayerMonthPrepared)
def handle_offer_quests_for_new_month(*, context: PlayerMonthPrepared) -> Command:
    return OfferQuests(faction=context.faction, month=context.current_month)


@message_registry.register_event(event=PlayerMonthPrepared)
def handle_bring_quest_contracts_home_for_new_month(*, context: PlayerMonthPrepared) -> Command:
    return BringQuestContractsHome(faction=context.faction, month=context.current_month)
