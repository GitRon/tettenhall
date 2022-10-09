import itertools
import random
from dataclasses import dataclass


@dataclass
class DiceNotation:
    rolls: int
    sides: int

    def __str__(self):
        return f'{self.rolls}d{self.sides}'

    @property
    def result(self):
        result = 0
        for _ in itertools.repeat(None, self.rolls):
            result += random.randint(1, self.sides)
        return result


class RandomHelper:

    @staticmethod
    def throw_coin() -> bool:
        flip = random.randint(0, 1)
        if flip == 1:
            return True
        return False
