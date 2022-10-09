import itertools
import random
from typing import List

from apps.skirmish.domain import commands, helpers
from apps.skirmish.domain import model


# def create_random_warband(cmd:commands.CreateRandomWarband):
#     warrior_list = []
#     for _ in itertools.repeat(None, cmd.no_warriors):
#         warrior_list.append(model.Warrior.generate_random())
#
#     return warrior_list


def do_skirmish(cmd: commands.DoSkirmish):
    player_warrior_list: List[model.Warrior] = cmd.player_warrior_list
    opponent_warrior_list: List[model.Warrior] = cmd.opponent_warrior_list

    damage_delt = 0
    while damage_delt < 100:
        player_warrior = random.choice(player_warrior_list)
        opponent_warrior = random.choice(opponent_warrior_list)
        if helpers.RandomHelper.throw_coin():
            print(f'Player warrior {player_warrior} attacks {opponent_warrior}...')
            damage_delt += opponent_warrior.defends_attack(attack=player_warrior.attack)
        else:
            print(f'Opponent warrior {opponent_warrior} attacks {player_warrior}...')
            damage_delt += player_warrior.defends_attack(attack=opponent_warrior.attack)
