from apps.warband.faction.domain.rival_policy import (
    BuyFromShop,
    DraftFromFyrd,
    HallUpgradeOffer,
    HireFromPub,
    PubOffer,
    RivalMonthSnapshot,
    RivalPolicy,
    ShopOffer,
    UpgradeHall,
)


def _snapshot(
    *,
    fyrd_reserve: int = 0,
    purse: int = 1000,
    wage_bill: int = 0,
    draft_wage: int = 75,
    pub_offer_list: list[PubOffer] | None = None,
    shop_offer_list: list[ShopOffer] | None = None,
    held_gear_values: dict[str, list[float]] | None = None,
    warriors_on_payroll: int = 0,
    hall_upgrade: HallUpgradeOffer | None = None,
) -> RivalMonthSnapshot:
    return RivalMonthSnapshot(
        fyrd_reserve=fyrd_reserve,
        purse=purse,
        wage_bill=wage_bill,
        draft_wage=draft_wage,
        pub_offer_list=pub_offer_list or [],
        shop_offer_list=shop_offer_list or [],
        held_gear_values=held_gear_values or {},
        warriors_on_payroll=warriors_on_payroll,
        hall_upgrade=hall_upgrade,
    )


def _sword(*, item_id: int = 1, price: int = 50, value: float = 7) -> ShopOffer:
    return ShopOffer(item_id=item_id, price=price, slot="weapon", value=value)


def _small_hall() -> HallUpgradeOffer:
    return HallUpgradeOffer(current_level=0, new_level=1, price=600)


def test_decide_drafts_while_the_purse_covers_the_wage_bill_with_the_levy_on_it():
    assert RivalPolicy.decide(snapshot=_snapshot(fyrd_reserve=2, purse=225, wage_bill=150)) == [DraftFromFyrd()]


def test_decide_drafts_nobody_the_purse_cannot_keep():
    """
    A draft is free, but the levy is paid from next month: 200 covers the 150 the roster draws, and not
    the 75 he would add to it.
    """
    assert RivalPolicy.decide(snapshot=_snapshot(fyrd_reserve=2, purse=200, wage_bill=150)) == []


def test_decide_drafts_once_a_month_whatever_the_reserve_holds():
    assert RivalPolicy.decide(snapshot=_snapshot(fyrd_reserve=5)) == [DraftFromFyrd()]


def test_decide_hires_beside_the_draft():
    """
    The levy scores 1000 over six months of his 75, the mercenary 1000 over his 200 and six months of
    100 - so the draft goes first, and the 1000 still keeps them both.
    """
    snapshot = _snapshot(fyrd_reserve=1, pub_offer_list=[PubOffer(warrior_id=7, hiring_price=200, monthly_salary=100)])

    assert RivalPolicy.decide(snapshot=snapshot) == [DraftFromFyrd(), HireFromPub(warrior_id=7)]


def test_decide_hires_before_it_buys():
    """
    A man scores 1000 over 800 (his price and six months' wage), above the sword's
    10 times 5 over 50 - so he is taken first, and the sword still fits in the purse he leaves.
    """
    snapshot = _snapshot(
        pub_offer_list=[PubOffer(warrior_id=7, hiring_price=200, monthly_salary=100)],
        shop_offer_list=[_sword()],
        held_gear_values={"weapon": [2]},
    )

    assert RivalPolicy.decide(snapshot=snapshot) == [HireFromPub(warrior_id=7), BuyFromShop(item_id=1)]


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


def test_decide_takes_a_man_who_costs_nothing_at_all():
    snapshot = _snapshot(purse=0, pub_offer_list=[PubOffer(warrior_id=3, hiring_price=0, monthly_salary=0)])

    assert RivalPolicy.decide(snapshot=snapshot) == [HireFromPub(warrior_id=3)]


def test_decide_buys_an_item_that_lifts_the_weakest_man():
    snapshot = _snapshot(shop_offer_list=[_sword()], held_gear_values={"weapon": [7, 2]})

    assert RivalPolicy.decide(snapshot=snapshot) == [BuyFromShop(item_id=1)]


def test_decide_buys_nothing_that_lifts_nobody():
    snapshot = _snapshot(shop_offer_list=[_sword(value=5)], held_gear_values={"weapon": [7, 5]})

    assert RivalPolicy.decide(snapshot=snapshot) == []


def test_decide_weighs_a_second_item_against_what_the_first_left_behind():
    """
    The first sword lifts the man at 2 to 7. The second, at 5, would have lifted him too, but he now
    holds the 7 and so does everybody else - there is nobody left for it to lift.
    """
    snapshot = _snapshot(
        shop_offer_list=[_sword(item_id=1, value=7), _sword(item_id=2, value=5)],
        held_gear_values={"weapon": [7, 2]},
    )

    assert RivalPolicy.decide(snapshot=snapshot) == [BuyFromShop(item_id=1)]


def test_decide_buys_nothing_for_a_band_with_nobody_to_carry_it():
    assert RivalPolicy.decide(snapshot=_snapshot(shop_offer_list=[_sword()])) == []


def test_decide_buys_nothing_offered_at_no_price():
    snapshot = _snapshot(shop_offer_list=[_sword(price=0)], held_gear_values={"weapon": [2]})

    assert RivalPolicy.decide(snapshot=snapshot) == []


def test_decide_buys_nothing_whose_gain_is_not_worth_its_price():
    # Half a point over the weakest man, for 100 silver, scores 0.05 - below MIN_SCORE
    snapshot = _snapshot(shop_offer_list=[_sword(price=100, value=2.5)], held_gear_values={"weapon": [2]})

    assert RivalPolicy.decide(snapshot=snapshot) == []


def test_decide_keeps_the_wage_bill_covered_after_a_purchase():
    snapshot = _snapshot(purse=120, wage_bill=100, shop_offer_list=[_sword()], held_gear_values={"weapon": [2]})

    assert RivalPolicy.decide(snapshot=snapshot) == []


def test_decide_raises_the_hall_once_the_man_it_drafts_is_on_the_payroll():
    """
    With nobody on the payroll a Small Hall pays the 50 a town without one does, and is worth nothing.
    The levy is taken first, and the hall he mans then pays 250 more a month: six months of that over
    its 600 scores 2.5. The 400 left still covers his wage.
    """
    snapshot = _snapshot(fyrd_reserve=1, hall_upgrade=_small_hall())

    assert RivalPolicy.decide(snapshot=snapshot) == [DraftFromFyrd(), UpgradeHall(new_level=1, price=600)]


def test_decide_raises_the_hall_before_a_man_it_outscores():
    # 2.5 for the hall, against 1000 over six months of a 75 wage for the levy - 2.2
    snapshot = _snapshot(fyrd_reserve=1, warriors_on_payroll=1, hall_upgrade=_small_hall())

    assert RivalPolicy.decide(snapshot=snapshot) == [UpgradeHall(new_level=1, price=600), DraftFromFyrd()]


def test_decide_raises_no_hall_with_nobody_on_the_payroll_to_man_it():
    assert RivalPolicy.decide(snapshot=_snapshot(hall_upgrade=_small_hall())) == []


def test_decide_raises_no_hall_the_purse_cannot_keep_the_wages_after():
    snapshot = _snapshot(purse=650, wage_bill=100, warriors_on_payroll=1, hall_upgrade=_small_hall())

    assert RivalPolicy.decide(snapshot=snapshot) == []
