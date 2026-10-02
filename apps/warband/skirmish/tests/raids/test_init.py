import pytest

from apps.warband.skirmish.choices.raid_kind import RaidKindChoices
from apps.warband.skirmish.raids import get_raid_kind
from apps.warband.skirmish.raids.kinds import BurnTheVillage


def test_get_raid_kind_reads_the_stored_value():
    assert get_raid_kind(value=RaidKindChoices.BURN_THE_VILLAGE) is BurnTheVillage


def test_get_raid_kind_refuses_a_value_nothing_is_stored_as():
    with pytest.raises(RuntimeError, match=r"No raid kind is stored as 99\."):
        get_raid_kind(value=99)
