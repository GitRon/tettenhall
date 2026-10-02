from queuebie import message_registry
from queuebie.messages import Command

from apps.warband.quest.messages.events.quest_contract import QuestContractReturned
from apps.warband.warrior.messages.commands.warrior import GrantRenown


@message_registry.register_event(event=QuestContractReturned)
def handle_quest_renown(*, context: QuestContractReturned) -> list[Command] | None:
    # Every man who came home is known for it, the same amount each: the band did the errand together
    if context.outcome.renown_per_man == 0:
        return None

    return [
        GrantRenown(
            warrior=warrior,
            faction=context.faction,
            renown=context.outcome.renown_per_man,
            month=context.month,
        )
        for warrior in context.warriors
    ]
