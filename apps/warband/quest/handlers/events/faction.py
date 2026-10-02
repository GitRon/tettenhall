from queuebie import message_registry
from queuebie.messages import Command

from apps.warband.faction.messages.events.faction import NewFactionCreated
from apps.warband.quest.messages.commands.quest import OfferQuests


@message_registry.register_event(event=NewFactionCreated)
def handle_offer_quests_for_new_faction(*, context: NewFactionCreated) -> Command | None:
    # The first month's board, which no month turn draws. The player's alone, as every month's is
    if not context.is_player:
        return None

    return OfferQuests(faction=context.faction, month=context.current_month)
