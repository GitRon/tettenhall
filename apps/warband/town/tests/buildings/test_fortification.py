import pytest

from apps.warband.town.buildings.base import BuildingEffect
from apps.warband.town.buildings.fortification import (
    NPC_STARTING_FORTIFICATION_LEVEL,
    BurhWall,
    Earthwork,
    Fortification,
    NoFortification,
    Palisade,
)
from apps.warband.town.models import Town


def test_get_building_by_type_without_a_fortification():
    result = Fortification.get_building_by_type(building_type=Town.FortificationChoices.FORTIFICATION_NONE)

    assert isinstance(result, NoFortification)


def test_get_building_by_type_small():
    result = Fortification.get_building_by_type(building_type=Town.FortificationChoices.FORTIFICATION_SMALL)

    assert isinstance(result, Palisade)


def test_get_building_by_type_medium():
    result = Fortification.get_building_by_type(building_type=Town.FortificationChoices.FORTIFICATION_MEDIUM)

    assert isinstance(result, Earthwork)


def test_get_building_by_type_large():
    result = Fortification.get_building_by_type(building_type=Town.FortificationChoices.FORTIFICATION_LARGE)

    assert isinstance(result, BurhWall)


def test_get_building_by_type_unknown_level():
    with pytest.raises(RuntimeError, match="Unknown fortification type: 4"):
        Fortification.get_building_by_type(building_type=4)


def test_get_levels_matches_the_model_choices():
    """
    The level is written straight into a choices-constrained column and Django validates choices only
    in forms, so a variant added here without its counterpart on the model would store a level the
    display and the admin cannot handle.
    """
    assert len(Fortification.get_levels()) == len(Town.FortificationChoices)


def test_no_fortification_leaves_the_town_in_the_open():
    """
    The one family whose level 0 is no effect at all: a march on a town without a wall is fought in the
    open, so there is no cover to break and no defence bonus to hand out.
    """
    assert NoFortification.FORTIFICATION_STRENGTH == 0


def test_get_effects_names_the_wall_strength():
    result = Earthwork.get_effects()

    assert result == (BuildingEffect(label="Wall strength when marched on", value="35 points"),)


def test_npc_starting_fortification_level_is_the_palisade():
    """
    The level a rival is created with, and the only one it ever has. Derived from get_levels() rather
    than written as a number, so this pins the variant it resolves to rather than the index.
    """
    result = Fortification.get_building_by_type(building_type=NPC_STARTING_FORTIFICATION_LEVEL)

    assert isinstance(result, Palisade)
    assert result.FORTIFICATION_STRENGTH == 20


def test_npc_starting_fortification_level_is_a_level_the_column_accepts():
    """
    The constant is written straight into a choices-constrained column, and Django validates choices
    only in forms.
    """
    assert NPC_STARTING_FORTIFICATION_LEVEL == Town.FortificationChoices.FORTIFICATION_SMALL
