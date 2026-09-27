from queuebie.messages import Command

from apps.warband.skirmish.messages.commands.skirmish import WarriorAttacksWarrior
from apps.warband.skirmish.services.actions.base import SkirmishActionService


class SimpleAttackService(SkirmishActionService):
    command: Command = WarriorAttacksWarrior
