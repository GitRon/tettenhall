from queuebie import message_registry
from queuebie.messages import Command

from apps.warband.faction.messages.commands.warrior import RecruitWarriorFromQuest
from apps.warband.quest.messages.events.quest_contract import QuestContractReturned


@message_registry.register_event(event=QuestContractReturned)
def handle_quest_warrior(*, context: QuestContractReturned) -> Command | None:
    if context.outcome.warrior_generator_class is None:
        return None

    return RecruitWarriorFromQuest(
        faction=context.faction,
        generator_class=context.outcome.warrior_generator_class,
        month=context.month,
    )
