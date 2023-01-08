from apps.core.domain import event_registry
from apps.core.domain.events import EventConsumer
from apps.skirmish.events import duel, warrior
from apps.skirmish.models.battle_history import BattleHistory
from apps.skirmish.models.skirmish import Skirmish


class BattleHistoryEventConsumer(EventConsumer):
    model = BattleHistory
    skirmish: Skirmish

    def __init__(self, skirmish: Skirmish, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.skirmish = skirmish

    @event_registry.register(event=warrior.WarriorTakesDamage)
    def handle_warrior_takes_damage(self, context: warrior.WarriorTakesDamage.Context):
        self.model.objects.create_record(
            skirmish=self.skirmish,
            message=f"{context.attacker} hits for {context.attacker_damage} damage and {context.defender} defends for "
            f"{context.defender_damage} resulting in {context.damage} damage.",
        )

    @event_registry.register(event=duel.DuelAttackerDefenderDecided)
    def handle_attacker_defender_decided(self, context: duel.DuelAttackerDefenderDecided.Context):
        self.model.objects.create_record(
            skirmish=self.skirmish,
            message=f"Warrior {context.attacker} is the attacker and warrior {context.defender} the defender.",
        )

    @event_registry.register(event=warrior.WarriorIsIncapacitated)
    def handle_warrior_incapacitation(self, context: warrior.WarriorIsIncapacitated.Context):
        self.model.objects.create_record(
            skirmish=self.skirmish,
            message=f"{warrior} is out of the fight being {context.condition}.",
        )
