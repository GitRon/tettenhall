from apps.core.event_loop.messages import Command
from apps.skirmish.messages.commands.skirmish import WarriorAttacksWarriorWithSimpleAttack
from apps.skirmish.services.actions.base import AttackService


class SimpleAttackService(AttackService):
    command: Command = WarriorAttacksWarriorWithSimpleAttack
    context: WarriorAttacksWarriorWithSimpleAttack.Context
