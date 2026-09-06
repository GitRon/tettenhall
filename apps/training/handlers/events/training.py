from queuebie import message_registry
from queuebie.messages import Command

from apps.faction.messages.events.faction import NewFactionCreated
from apps.month.messages.commands.month import CreatePlayerMonthLog
from apps.month.messages.events.month import FactionMonthPrepared
from apps.month.models.player_month_log import PlayerMonthLog
from apps.training.messages.commands.training import CreateNewTraining, TrainWarriors
from apps.training.messages.events.training import WarriorUpgradedSkill


@message_registry.register_event(event=NewFactionCreated)
def handle_create_training_for_faction(*, context: NewFactionCreated) -> Command:
    return CreateNewTraining(faction=context.faction)


@message_registry.register_event(event=WarriorUpgradedSkill)
def handle_warrior_upgraded_skill(*, context: WarriorUpgradedSkill) -> Command:
    return CreatePlayerMonthLog(
        title=f"Your warrior {context.warrior.name} upgraded his {context.changed_attribute}!",
        kind=PlayerMonthLog.KindChoices.KIND_SKILL_UPGRADE,
        month=context.month,
        faction=context.warrior.faction,
    )


# On the faction-wide event, so a war band the player leaves alone for ten months is a harder fight
# than it was. The regimen is not on the message: every faction owns its own row, and reading it is a
# query, which strict mode forbids here - so the command carries the faction and its handler looks up
# whose regimen that is
@message_registry.register_event(event=FactionMonthPrepared)
def handle_training_of_warriors_for_new_month(*, context: FactionMonthPrepared) -> list[Command]:
    return [TrainWarriors(faction=context.faction, month=context.current_month)]
