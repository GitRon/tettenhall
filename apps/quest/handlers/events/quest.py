import random

from queuebie import message_registry
from queuebie.messages import Command

from apps.quest.messages.events import quest
from apps.skirmish.messages.commands.skirmish import CreateSkirmish
from apps.warrior.services.generators.warrior.mercenary import MercenaryWarriorGenerator


@message_registry.register_event(event=quest.QuestAccepted)
def handle_create_skirmish_for_quest_contract(*, context: quest.QuestAccepted) -> list[Command] | Command:
    accepting_faction = context.accepting_faction
    target_faction = context.quest.target_faction
    # TODO: all those warriors are naked... we need to give them equipment
    warrior_generator = MercenaryWarriorGenerator(
        faction=target_faction, culture=target_faction.culture, savegame_id=context.accepting_faction.savegame_id
    )

    return CreateSkirmish(
        name=f"{context.quest.name} in {target_faction}",
        faction_1=accepting_faction,
        faction_2=target_faction,
        warrior_list_1=context.quest_contract.assigned_warriors.all(),
        warrior_list_2=[
            warrior_generator.process()
            for _ in range(random.randrange(*context.quest.get_min_max_number_of_opponents()))
        ],
        quest_contract=context.quest_contract,
    )
