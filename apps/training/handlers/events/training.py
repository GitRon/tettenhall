from apps.core.domain import message_registry
from apps.training.messages.events.training import WarriorUpgradedSkill
from apps.week.models.player_week_log import PlayerWeekLog


@message_registry.register_event(event=WarriorUpgradedSkill)
def handle_marketplace_mercenaries_restocked(*, context: WarriorUpgradedSkill.Context):
    PlayerWeekLog.objects.create_record(
        title=f"Your warrior {context.warrior.name} upgraded his {context.changed_attribute}!",
        message="Some fancy text",
        week=context.week,
        faction_id=context.warrior.faction_id,
    )
