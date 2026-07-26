from unittest import mock

import pytest

from apps.faction.handlers.events.faction import (
    handle_create_player_faction_for_new_savegame,
    handle_warriors_with_low_morale_determined,
)
from apps.faction.messages.commands.faction import CreateNewFaction
from apps.faction.messages.events.faction import FactionWarriorsWithLowMoraleDetermined
from apps.faction.tests.factories.culture import CultureFactory
from apps.faction.tests.factories.faction import FactionFactory
from apps.savegame.messages.events.savegame import NewSavegameCreated
from apps.savegame.tests.factories.savegame import SavegameFactory
from apps.skirmish.tests.factories.warrior import WarriorFactory
from apps.warrior.messages.commands.warrior import ReplenishWarriorMorale


@pytest.mark.django_db
def test_handle_create_player_faction_for_new_savegame_starts_with_the_player_faction():
    savegame = SavegameFactory()
    culture = CultureFactory()

    with mock.patch("apps.faction.handlers.events.faction.random.randint", return_value=3):
        result = handle_create_player_faction_for_new_savegame(
            context=NewSavegameCreated(
                savegame=savegame, faction_name="Wessex", town_name="Winchester", faction_culture_id=culture.id
            )
        )

    assert result[0] == CreateNewFaction(
        name="Wessex", savegame=savegame, culture_id=culture.id, is_player_faction=True
    )


@pytest.mark.django_db
def test_handle_create_player_faction_for_new_savegame_adds_the_drawn_number_of_rival_factions():
    savegame = SavegameFactory()
    culture = CultureFactory()

    with mock.patch("apps.faction.handlers.events.faction.random.randint", return_value=3):
        result = handle_create_player_faction_for_new_savegame(
            context=NewSavegameCreated(
                savegame=savegame, faction_name="Wessex", town_name="Winchester", faction_culture_id=culture.id
            )
        )

    assert len(result) == 4
    assert result[3].is_player_faction is False


def test_handle_warriors_with_low_morale_determined_with_warriors():
    faction = FactionFactory.build()
    warrior = WarriorFactory.build(faction=faction)

    result = handle_warriors_with_low_morale_determined(
        context=FactionWarriorsWithLowMoraleDetermined(faction=faction, warrior_list=[warrior], month=3)
    )

    assert result == [ReplenishWarriorMorale(warrior=warrior, month=3)]


def test_handle_warriors_with_low_morale_determined_without_warriors():
    faction = FactionFactory.build()

    result = handle_warriors_with_low_morale_determined(
        context=FactionWarriorsWithLowMoraleDetermined(faction=faction, warrior_list=[], month=3)
    )

    assert result == []
