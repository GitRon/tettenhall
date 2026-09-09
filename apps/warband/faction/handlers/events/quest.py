from queuebie import message_registry
from queuebie.messages import Command

from apps.warband.faction.messages.commands.quest import OfferNewQuestsOnBulletinBoard
from apps.warband.faction.messages.events.faction import NewFactionCreated
from apps.warband.month.messages.events.month import PlayerMonthPrepared


@message_registry.register_event(event=NewFactionCreated)
@message_registry.register_event(event=PlayerMonthPrepared)
def handle_offer_new_quests_on_bulletin_board(*, context: PlayerMonthPrepared | NewFactionCreated) -> Command:
    return OfferNewQuestsOnBulletinBoard(faction=context.faction, month=context.current_month)
