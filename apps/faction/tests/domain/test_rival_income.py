from apps.faction.domain.rival_income import RivalIncome


def test_get_monthly_income_scales_with_the_war_band():
    # 50 of baseline plus 200 a man
    assert RivalIncome.get_monthly_income(healthy_warriors=3) == 650


def test_get_monthly_income_for_a_faction_that_fields_nobody():
    """
    The baseline alone, which is well under a single salary - a faction that cannot field a warrior
    is meant to be under pressure, not earning its way out of it.
    """
    assert RivalIncome.get_monthly_income(healthy_warriors=0) == 50
