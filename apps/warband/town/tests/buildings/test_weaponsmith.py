import itertools

import pytest

from apps.warband.town.buildings.base import BuildingEffect
from apps.warband.town.buildings.weaponsmith import (
    LargeWeaponsmith,
    MediumWeaponsmith,
    NoWeaponsmith,
    SmallWeaponsmith,
    Weaponsmith,
)
from apps.warband.town.models import Town


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


def test_get_effects_names_the_best_band_the_quality_bonus_and_the_upgrade_cap():
    result = SmallWeaponsmith.get_effects()

    assert result == (
        BuildingEffect(label="Best gear in the shop", value="Fine"),
        BuildingEffect(label="Quality of the shop's wares", value="+1"),
        BuildingEffect(label="Best a smith makes of old gear", value="Cheap"),
    )


def test_get_effects_without_a_weaponsmith_names_the_rustic_band_and_no_upgrade():
    result = NoWeaponsmith.get_effects()

    assert result[0::2] == (
        BuildingEffect(label="Best gear in the shop", value="Rustic"),
        BuildingEffect(label="Best a smith makes of old gear", value="Nothing"),
    )


def test_can_upgrade_item_only_with_a_forge():
    assert [level.can_upgrade_item() for level in Weaponsmith.get_levels()] == [False, True, True, True]


def test_max_upgrade_condition_rises_up_the_ladder():
    """
    A forge that is raised and then reworks less than before would be a building the player pays to lose.
    """
    for lower, higher in itertools.pairwise(Weaponsmith.get_levels()[1:]):
        assert lower.MAX_UPGRADE_CONDITION < higher.MAX_UPGRADE_CONDITION


def test_shop_item_tiers_never_narrow_up_the_ladder():
    """
    A forge that is raised and then stocks less than before would be a building the player pays to lose.
    """
    for lower, higher in itertools.pairwise(Weaponsmith.get_levels()):
        assert lower.SHOP_ITEM_TIERS <= higher.SHOP_ITEM_TIERS
