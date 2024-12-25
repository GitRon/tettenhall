import random

from apps.core.domain import message_registry
from apps.quest.messages.events import quest
from apps.skirmish.messages.commands.skirmish import CreateSkirmish
from apps.warrior.services.generators.warrior.mercenary import MercenaryWarriorGenerator


@message_registry.register_event(event=quest.QuestAccepted)
def handle_create_skirmish_for_quest_contract(*, context: quest.QuestAccepted.Context):
    accepting_faction = context.accepting_faction
    warrior_generator = MercenaryWarriorGenerator(faction=accepting_faction, culture=accepting_faction.culture)

    # TODO: add a name here based on the quest and the target faction
    # TODO: we need to set the skirmish in the quest contract somehow... but how? put the FK in the skirmish model?
    return CreateSkirmish(
        context=CreateSkirmish.Context(
            faction_1=accepting_faction,
            faction_2=context.quest.faction,
            warrior_list_1=context.quest_contract.assigned_warriors.all(),
            warrior_list_2=[warrior_generator.process() for x in range(random.randrange(3, 5))],
        )
    )
