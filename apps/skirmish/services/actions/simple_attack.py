from apps.core.event_loop.messages import Command
from apps.skirmish.messages.commands.skirmish import WarriorAttacksWarrior
from apps.skirmish.services.actions.base import AttackService


class SimpleAttackService(AttackService):
    command: Command = WarriorAttacksWarrior
