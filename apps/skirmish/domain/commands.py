from dataclasses import dataclass


class Command:
    pass


@dataclass
class CreateRandomWarband(Command):
    no_warriors: int


@dataclass
class DoSkirmish(Command):
    player_warrior_list: list
    opponent_warrior_list: list
