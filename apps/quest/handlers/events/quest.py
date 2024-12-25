import random

from apps.core.domain import message_registry
from apps.quest.messages.events import quest
from apps.skirmish.messages.commands.skirmish import CreateSkirmish
from apps.skirmish.messages.events import skirmish
from apps.warrior.services.generators.warrior.mercenary import MercenaryWarriorGenerator


@message_registry.register_event(event=quest.QuestAccepted)
def handle_create_skirmish_for_quest_contract(*, context: quest.QuestAccepted.Context):
    accepting_faction = context.accepting_faction
    warrior_generator = MercenaryWarriorGenerator(faction=accepting_faction, culture=accepting_faction.culture)

    return CreateSkirmish(
        context=CreateSkirmish.Context(
            name=f"{context.quest.name} in {context.quest.faction}",
            faction_1=accepting_faction,
            faction_2=context.quest.faction,
            warrior_list_1=context.quest_contract.assigned_warriors.all(),
            # TODO: 3-5 should depend on the quest difficulty
            warrior_list_2=[warrior_generator.process() for _ in range(random.randrange(3, 5))],
            quest_contract=context.quest_contract,
        )
    )


@message_registry.register_event(event=skirmish.SkirmishCreated)
def handle_link_quest_contract_to_its_skirmish(*, context: skirmish.SkirmishCreated.Context):
    quest_contract = context.quest_contract
    quest_contract.skirmish = context.skirmish
    quest_contract.save()
