import pytest

from apps.town.buildings.base import BuildingEffect
from apps.town.buildings.sanctuary import (
    NPC_STARTING_SANCTUARY_LEVEL,
    LargeSanctuary,
    MediumSanctuary,
    NoSanctuary,
    Sanctuary,
    SmallSanctuary,
)
from apps.town.models import Town


def test_get_building_by_type_without_a_sanctuary():
    result = Sanctuary.get_building_by_type(building_type=Town.SanctuaryChoices.SANCTUARY_NONE)

    assert isinstance(result, NoSanctuary)


def test_get_building_by_type_small():
    result = Sanctuary.get_building_by_type(building_type=Town.SanctuaryChoices.SANCTUARY_SMALL)

    assert isinstance(result, SmallSanctuary)


def test_get_building_by_type_medium():
    result = Sanctuary.get_building_by_type(building_type=Town.SanctuaryChoices.SANCTUARY_MEDIUM)

    assert isinstance(result, MediumSanctuary)


def test_get_building_by_type_large():
    result = Sanctuary.get_building_by_type(building_type=Town.SanctuaryChoices.SANCTUARY_LARGE)

    assert isinstance(result, LargeSanctuary)


def test_get_building_by_type_unknown_level():
    with pytest.raises(RuntimeError, match="Unknown sanctuary type: 4"):
        Sanctuary.get_building_by_type(building_type=4)


def test_get_levels_matches_the_model_choices():
    """
    The level is written straight into a choices-constrained column and Django validates choices only
    in forms, so a variant added here without its counterpart on the model would store a level the
    display and the admin cannot handle.
    """
    assert len(Sanctuary.get_levels()) == len(Town.SanctuaryChoices)


def test_get_effects_names_the_healing_ceiling():
    result = SmallSanctuary.get_effects()

    assert result == (BuildingEffect(label="Healed per month at most", value="8 health points"),)


def test_npc_starting_sanctuary_level_is_the_shrine():
    """
    The level a rival is created with, and the only one it ever has. Derived from get_levels() rather
    than written as a number, so this pins the variant it resolves to rather than the index.
    """
    result = Sanctuary.get_building_by_type(building_type=NPC_STARTING_SANCTUARY_LEVEL)

    assert isinstance(result, SmallSanctuary)
    assert result.MAX_HEALING_POINTS == 8


def test_npc_starting_sanctuary_level_is_a_level_the_column_accepts():
    """
    The constant is written straight into a choices-constrained column, and Django validates choices
    only in forms.
    """
    assert NPC_STARTING_SANCTUARY_LEVEL == Town.SanctuaryChoices.SANCTUARY_SMALL
