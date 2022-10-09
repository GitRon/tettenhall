import itertools
import logging

from apps.skirmish.domain import commands, model
from apps.skirmish.service import message_bus, handlers

logger = logging.getLogger(__name__)

COMMAND_HANDLERS = {
    # commands.CreateRandomWarband: handlers.create_random_warband,
    commands.DoSkirmish: handlers.do_skirmish,
}
EVENT_HANDLERS = {
}

message_bus = message_bus.MessageBus(command_handlers=COMMAND_HANDLERS, event_handlers=EVENT_HANDLERS)


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    # cmd = commands.CreateRandomWarband(no_warriors=5)
    # message_bus.handle(cmd)

    warrior_list_1 = []
    for _ in itertools.repeat(None, 5):
        warrior_list_1.append(model.Warrior.generate_random())

    warrior_list_2 = []
    for _ in itertools.repeat(None, 5):
        warrior_list_2.append(model.Warrior.generate_random())

    cmd = commands.DoSkirmish(
        player_warrior_list=warrior_list_1,
        opponent_warrior_list=warrior_list_2,
    )
    message_bus.handle(cmd)
