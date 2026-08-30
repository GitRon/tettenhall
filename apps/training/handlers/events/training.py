from queuebie import message_registry
from queuebie.messages import Command

from apps.faction.messages.events.faction import NewFactionCreated
from apps.month.messages.commands.month import CreatePlayerMonthLog
from apps.month.messages.events.month import PlayerMonthPrepared
from apps.training.messages.commands.training import CreateNewTraining, TrainWarriors
from apps.training.messages.events.training import WarriorUpgradedSkill


@message_registry.register_event(event=NewFactionCreated)
def handle_create_training_for_faction(*, context: NewFactionCreated) -> Command:
    return CreateNewTraining(faction=context.faction)


@message_registry.register_event(event=WarriorUpgradedSkill)
def handle_warrior_upgraded_skill(*, context: WarriorUpgradedSkill) -> Command:
    return CreatePlayerMonthLog(
        title=f"Your warrior {context.warrior.name} upgraded his {context.changed_attribute}!",
        month=context.month,
        faction=context.warrior.faction,
    )


@message_registry.register_event(event=PlayerMonthPrepared)
def handle_training_of_warriors_for_new_month(*, context: PlayerMonthPrepared) -> list[Command]:
    # A savegame whose player faction has no training row has nothing to train, and the command
    # handler dereferences "training" unguarded - finishing the month would answer with a 500
    if context.training is None:
        return []

    return [TrainWarriors(faction=context.faction, training=context.training, month=context.current_month)]
