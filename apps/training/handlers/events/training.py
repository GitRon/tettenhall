from apps.core.domain import message_registry
from apps.core.event_loop.messages import Command
from apps.training.messages.commands.training import TrainWarriors
from apps.training.messages.events.training import WarriorUpgradedSkill
from apps.week.messages.events.week import WeekPrepared
from apps.week.models.player_week_log import PlayerWeekLog


@message_registry.register_event(event=WarriorUpgradedSkill)
def handle_marketplace_mercenaries_restocked(*, context: WarriorUpgradedSkill.Context):
    PlayerWeekLog.objects.create_record(
        title=f"Your warrior {context.warrior.name} upgraded his {context.changed_attribute}!",
        week=context.week,
        faction_id=context.warrior.faction_id,
    )


@message_registry.register_event(event=WeekPrepared)
def handle_training_of_warriors_for_new_week(*, context: WeekPrepared.Context) -> list[Command]:
    return [
        TrainWarriors(
            TrainWarriors.Context(faction=context.faction, training=context.training, week=context.current_week)
        )
    ]
