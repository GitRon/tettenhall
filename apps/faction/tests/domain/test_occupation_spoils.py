from apps.faction.domain.occupation_spoils import OccupationSpoils


def test_get_plundered_silver_takes_the_share():
    assert OccupationSpoils.get_plundered_silver(treasury=1000) == 500


def test_get_plundered_silver_of_an_empty_treasury():
    assert OccupationSpoils.get_plundered_silver(treasury=0) == 0


def test_get_plundered_silver_of_a_faction_in_the_red():
    assert OccupationSpoils.get_plundered_silver(treasury=-400) == 0
