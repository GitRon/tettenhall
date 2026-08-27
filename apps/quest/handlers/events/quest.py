from queuebie import message_registry
from queuebie.messages import Command

from apps.quest.messages.events import quest
from apps.skirmish.messages.commands.skirmish import CreateSkirmish


@message_registry.register_event(event=quest.QuestAccepted)
def handle_create_skirmish_for_quest_contract(*, context: quest.QuestAccepted) -> list[Command] | Command:
    # Nothing but mapping here: both rosters were resolved by the command handler that raised this
    return CreateSkirmish(
        name=f"{context.quest.name} in {context.target_faction}",
        faction_1=context.accepting_faction,
        faction_2=context.target_faction,
        warrior_list_1=context.quest_contract.assigned_warriors.all(),
        warrior_list_2=context.target_warriors,
        month=context.month,
        quest_contract=context.quest_contract,
    )
