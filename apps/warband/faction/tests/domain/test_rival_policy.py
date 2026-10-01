from apps.warband.faction.domain.rival_policy import (
    DraftFromFyrd,
    HireFromPub,
    PubOffer,
    RivalMonthSnapshot,
    RivalPolicy,
)


def _snapshot(
    *, fyrd_reserve: int = 0, purse: int = 1000, wage_bill: int = 0, pub_offer_list: list[PubOffer] | None = None
) -> RivalMonthSnapshot:
    return RivalMonthSnapshot(
        fyrd_reserve=fyrd_reserve, purse=purse, wage_bill=wage_bill, pub_offer_list=pub_offer_list or []
    )


def test_decide_drafts_while_the_purse_covers_the_wage_bill():
    assert RivalPolicy.decide(snapshot=_snapshot(fyrd_reserve=2, purse=150, wage_bill=150)) == [DraftFromFyrd()]


def test_decide_drafts_nobody_the_purse_cannot_keep():
    """
    A draft is free, so what it commits the faction to is the man's keep - which is why the purse has
    to still cover the roster's wage bill once over rather than any purchase price.
    """
    assert RivalPolicy.decide(snapshot=_snapshot(fyrd_reserve=2, purse=100, wage_bill=150)) == []


def test_decide_hires_nobody_while_the_fyrd_has_men():
    """
    He is affordable, but one free man still stands in the fyrd. The reserve is the brake on a rival's
    growth, so the pub waits until it is empty - and the draft is all the month brings.
    """
    snapshot = _snapshot(fyrd_reserve=1, pub_offer_list=[PubOffer(warrior_id=1, hiring_price=200, monthly_salary=100)])

    assert RivalPolicy.decide(snapshot=snapshot) == [DraftFromFyrd()]


def test_decide_hires_a_man_the_purse_can_keep():
    # 1000 less his price of 200 still covers his wage of 100
    snapshot = _snapshot(pub_offer_list=[PubOffer(warrior_id=7, hiring_price=200, monthly_salary=100)])

    assert RivalPolicy.decide(snapshot=snapshot) == [HireFromPub(warrior_id=7)]


def test_decide_passes_over_a_man_the_purse_cannot_keep():
    """
    250 pays his price of 200, but leaves 50 against the wage of 100 he would draw - so the purse would
    not cover the wage bill once over, and the rival leaves him standing.
    """
    snapshot = _snapshot(purse=250, pub_offer_list=[PubOffer(warrior_id=7, hiring_price=200, monthly_salary=100)])

    assert RivalPolicy.decide(snapshot=snapshot) == []


def test_decide_hires_cheapest_first_out_of_a_purse_it_keeps_count_of():
    """
    The cheap man first: 500 less 200 leaves 300 against his wage of 100. What is left is then 300 with
    a wage bill of 100, and the dearer man's 300 would leave nothing against 250 of wages. Weighing each
    man against the opening purse would take him too; taking the dearer man first would leave the cheap
    one out.
    """
    snapshot = _snapshot(
        purse=500,
        pub_offer_list=[
            PubOffer(warrior_id=1, hiring_price=300, monthly_salary=150),
            PubOffer(warrior_id=2, hiring_price=200, monthly_salary=100),
        ],
    )

    assert RivalPolicy.decide(snapshot=snapshot) == [HireFromPub(warrior_id=2)]


def test_decide_breaks_a_tie_on_price_by_the_man_who_came_first():
    snapshot = _snapshot(
        purse=500,
        pub_offer_list=[
            PubOffer(warrior_id=9, hiring_price=200, monthly_salary=100),
            PubOffer(warrior_id=4, hiring_price=200, monthly_salary=100),
        ],
    )

    assert RivalPolicy.decide(snapshot=snapshot) == [HireFromPub(warrior_id=4)]
