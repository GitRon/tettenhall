import pytest

from apps.town.buildings.weaponsmith import (
    LargeWeaponsmith,
    MediumWeaponsmith,
    NoWeaponsmith,
    SmallWeaponsmith,
    Weaponsmith,
)
from apps.town.models import Town


def test_get_building_by_type_without_a_weaponsmith():
    result = Weaponsmith.get_building_by_type(building_type=Town.WeaponsmithChoices.WEAPONSMITH_NONE)

    assert isinstance(result, NoWeaponsmith)


def test_get_building_by_type_small():
    result = Weaponsmith.get_building_by_type(building_type=Town.WeaponsmithChoices.WEAPONSMITH_SMALL)

    assert isinstance(result, SmallWeaponsmith)


def test_get_building_by_type_medium():
    result = Weaponsmith.get_building_by_type(building_type=Town.WeaponsmithChoices.WEAPONSMITH_MEDIUM)

    assert isinstance(result, MediumWeaponsmith)


def test_get_building_by_type_large():
    result = Weaponsmith.get_building_by_type(building_type=Town.WeaponsmithChoices.WEAPONSMITH_LARGE)

    assert isinstance(result, LargeWeaponsmith)


def test_get_building_by_type_unknown_level():
    with pytest.raises(RuntimeError, match="Unknown weaponsmith type: 4"):
        Weaponsmith.get_building_by_type(building_type=4)


def test_get_levels_matches_the_model_choices():
    """
    The level is written straight into a choices-constrained column and Django validates choices only
    in forms, so a variant added here without its counterpart on the model would store a level the
    display and the admin cannot handle.
    """
    assert len(Weaponsmith.get_levels()) == len(Town.WeaponsmithChoices)
