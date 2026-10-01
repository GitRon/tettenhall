import random

import pytest

from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.savegame.models.savegame import Savegame
from apps.warband.savegame.tests.factories.savegame import SavegameFactory
from apps.warband.skirmish.tests.factories.warrior import WarriorFactory
from scripts.playtest.policy import POLICIES
from scripts.playtest.report import GameReport


@pytest.fixture
def player_savegame(db) -> Savegame:
    """
    A running savegame whose player faction has a leader and nothing else: no fyrd, no silver, no rival.

    Each test adds the one thing the step under test reacts to, so a step that fires is one the test
    asked for.
    """
    savegame = SavegameFactory()
    faction = FactionFactory(savegame=savegame, fyrd_reserve=0)
    faction.leader = WarriorFactory(faction=faction)
    faction.save()
    savegame.player_faction = faction
    savegame.save()

    return savegame


@pytest.fixture
def report() -> GameReport:
    return GameReport(seed=1, policy=POLICIES["aggressive"].name)


@pytest.fixture
def rng() -> random.Random:
    return random.Random(1)
