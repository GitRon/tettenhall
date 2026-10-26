from apps.warband.skirmish.choices.turning_point import TurningPointChoices
from apps.warband.skirmish.domain.turning_point import is_in_trouble, most_important


def test_is_in_trouble_below_half_his_health():
    assert is_in_trouble(current_health=9, max_health=20) is True


def test_is_in_trouble_is_false_at_exactly_half():
    """
    "Below half" is the rule, so a leader standing at exactly half has not crossed it yet.
    """
    assert is_in_trouble(current_health=10, max_health=20) is False


def test_most_important_puts_a_threatened_leader_first():
    result = most_important(
        turning_points=[
            TurningPointChoices.MAN_DOWN,
            TurningPointChoices.ENEMY_LEADER_EXPOSED,
            TurningPointChoices.LEADER_THREATENED,
        ]
    )

    assert result == TurningPointChoices.LEADER_THREATENED


def test_most_important_puts_a_man_down_before_an_exposed_enemy():
    result = most_important(turning_points=[TurningPointChoices.ENEMY_LEADER_EXPOSED, TurningPointChoices.MAN_DOWN])

    assert result == TurningPointChoices.MAN_DOWN


def test_most_important_of_nothing_is_nothing():
    assert most_important(turning_points=[]) is None
