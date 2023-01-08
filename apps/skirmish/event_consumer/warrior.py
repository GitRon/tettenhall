from apps.core.domain import event_registry
from apps.core.domain.events import EventConsumer
from apps.skirmish.events import warrior
from apps.skirmish.models.warrior import Warrior


class WarriorEventConsumer(EventConsumer):
    @event_registry.register(event=warrior.WarriorTakesDamage)
    def handle_warrior_takes_damage(self, context: warrior.WarriorTakesDamage.Context):
        # Reduce health
        Warrior.objects.reduce_current_health(
            obj=context.defender,
            damage=context.damage,
        )

        # Update condition
        condition = Warrior.ConditionChoices.CONDITION_HEALTHY
        if context.defender.current_health < 0:
            if context.defender.current_health < context.defender.max_health * -0.15:
                condition = Warrior.ConditionChoices.CONDITION_DEAD
            else:
                condition = Warrior.ConditionChoices.CONDITION_UNCONSCIOUS

        Warrior.objects.set_condition(obj=context.defender, condition=condition)

        # todo trigger "WarriorIsIncapacitated" event
