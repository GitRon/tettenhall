from dataclasses import dataclass, field

from apps.warband.town.buildings.hall import Hall


@dataclass(frozen=True, kw_only=True)
class PubOffer:
    """
    One man standing in a rival's pub, as the policy weighs him.

    Priced before anything moves him, because his price is partly made of his wait - see
    [Warrior.hiring_price]. Keyed by id rather than carrying the warrior, so the policy never holds a
    model it could query through.
    """

    warrior_id: int
    hiring_price: int
    monthly_salary: int


@dataclass(frozen=True, kw_only=True)
class ShopOffer:
    """
    One item on a rival's own shelf, as the policy weighs it: what it costs, which slot it fills and
    what it is worth there - the same "expectancy_value" the gear hand-out ranks by.
    """

    item_id: int
    price: int
    slot: str
    value: float


@dataclass(frozen=True, kw_only=True)
class HallUpgradeOffer:
    """
    The next level of a rival's hall, offered only once "get_building_upgrade_refusal" has nothing
    against it - so the top level, the once-a-month rule and the price are the player's own guards.
    """

    current_level: int
    new_level: int
    price: int


@dataclass(frozen=True, kw_only=True)
class RivalMonthSnapshot:
    """
    What a rival knows about itself when it decides its month.

    The purse is the one the month opened with: nothing the month earns or spends reaches the ledger
    until every command the monthly handlers raised has run. The wage bill is the whole roster's, read
    off the same [Payroll] the salary run bills from - committed for this month, not yet debited.

    "held_gear_values" is what each man the hand-out may arm carries in each slot, one figure per man,
    an empty slot counting as the fallback's dice. "draft_wage" is what a levy the fyrd has not yet
    rolled is expected to draw.

    "warriors_on_payroll" is the men drawing a wage, the count the hall pays its revenue against (see
    [Hall.get_revenue_for_war_band]), and "hall_upgrade" the next level of the hall when it may be built.
    """

    fyrd_reserve: int
    purse: int
    wage_bill: int
    warriors_on_payroll: int
    draft_wage: int
    pub_offer_list: list[PubOffer]
    shop_offer_list: list[ShopOffer] = field(default_factory=list)
    held_gear_values: dict[str, list[float]] = field(default_factory=dict)
    hall_upgrade: HallUpgradeOffer | None = None


@dataclass(frozen=True, kw_only=True)
class DraftFromFyrd:
    pass


@dataclass(frozen=True, kw_only=True)
class HireFromPub:
    warrior_id: int


@dataclass(frozen=True, kw_only=True)
class BuyFromShop:
    item_id: int


@dataclass(frozen=True, kw_only=True)
class UpgradeHall:
    new_level: int
    price: int


type RivalDecision = DraftFromFyrd | HireFromPub | BuyFromShop | UpgradeHall


@dataclass(frozen=True, kw_only=True)
class _Candidate:
    decision: RivalDecision
    price: int
    added_wage: int
    # Settles a tie on score: a draft before a hire before an item before the hall, then the lower id
    order: tuple[int, int]
    # The shelf entry behind a purchase, None for anything else
    shop_offer: ShopOffer | None = None
    # The level behind a hall upgrade, None for anything else
    hall_offer: HallUpgradeOffer | None = None

    @property
    def is_man(self) -> bool:
        return self.shop_offer is None and self.hall_offer is None


class RivalPolicy:
    """
    What a rival does with its month, decided in one place.

    Pure: handed a snapshot, it returns decisions and touches neither the database nor the dice. The
    handler that asks it turns each decision into the same event the player's own button leads to, so a
    rival drafts, hires and buys through the player's commands rather than a second flow beside them.

    **One loop over everything the purse could go on.** Every candidate - the month's one fyrd draft,
    each man in the pub, each item on the shelf, the next level of the hall - is scored as
    "weight * need / what it costs", the best affordable one is taken, and the loop scores again on the
    purse, wage bill, payroll and gear that purchase left behind. It stops when nothing scores above
    MIN_SCORE, and the rest stays in the purse. Affordable means the purse still covers the wage bill
    once over after the purchase, the new man's wage included: a man is paid every month, an item and a
    building once.

    **The band is as large as the town carries.** A rival lives on its hall the way the player does, and
    the hall pays a flat revenue for the men it asks for, so every man past them is a wage with no income
    behind it. Nothing caps the band but that: the wage bill a man adds has to fit the purse, and the
    purse is refilled by the town alone.

    - **A man** is always needed. What he costs is his price plus WAGE_HORIZON_MONTHS of his wage, so a
      levy is taken before a hire, and a hire from the cheapest up.
    - **The hall** is worth the revenue its next level adds for the men on the payroll by then, over
      WAGE_HORIZON_MONTHS. A man taken earlier in the same month counts: he is on the payroll when the
      next month's revenue is paid.
    - **An item** is needed as far as it lifts the weakest man in its slot. The hand-out passes the best
      piece down the line, so buying it leaves the band holding the best of what it held plus the new
      one - the net gain is the new item over the weakest figure, and that figure is what it replaces.
      A man taken earlier in the same month adds nothing to what the band holds: his gear is not known
      until he is.

    The constants are balance numbers, measured with the harness (see "measuring-balance.md").
    """

    WAGE_HORIZON_MONTHS = 6
    MAN_WEIGHT = 1000
    ITEM_WEIGHT = 10
    BUILDING_WEIGHT = 1
    MIN_SCORE = 0.1

    @classmethod
    def decide(cls, *, snapshot: RivalMonthSnapshot) -> list[RivalDecision]:
        purse = snapshot.purse
        wage_bill = snapshot.wage_bill
        warriors_on_payroll = snapshot.warriors_on_payroll
        # Weakest first, so what a purchase replaces is always the head of the list
        held_gear_values = {slot: sorted(values) for slot, values in snapshot.held_gear_values.items()}
        candidate_list = cls._list_candidates(snapshot=snapshot)
        decision_list: list[RivalDecision] = []

        while True:
            scored_list = [
                (
                    cls._score(
                        candidate=candidate,
                        warriors_on_payroll=warriors_on_payroll,
                        held_gear_values=held_gear_values,
                    ),
                    candidate,
                )
                for candidate in candidate_list
                if purse - candidate.price >= wage_bill + candidate.added_wage
            ]
            scored_list = [(score, candidate) for score, candidate in scored_list if score > cls.MIN_SCORE]
            if not scored_list:
                return decision_list

            _best_score, best = min(scored_list, key=lambda pair: (-pair[0], pair[1].order))
            candidate_list.remove(best)
            purse -= best.price
            wage_bill += best.added_wage
            decision_list.append(best.decision)

            if best.is_man:
                warriors_on_payroll += 1
            elif best.shop_offer is not None:
                slot = best.shop_offer.slot
                held_gear_values[slot] = sorted([*held_gear_values[slot][1:], best.shop_offer.value])

    @staticmethod
    def _list_candidates(*, snapshot: RivalMonthSnapshot) -> list[_Candidate]:
        # One draft a month at most, whatever the reserve holds: the reserve is mustered a man at a time
        candidate_list = (
            [_Candidate(decision=DraftFromFyrd(), price=0, added_wage=snapshot.draft_wage, order=(0, 0))]
            if snapshot.fyrd_reserve > 0
            else []
        )
        candidate_list += [
            _Candidate(
                decision=HireFromPub(warrior_id=offer.warrior_id),
                price=offer.hiring_price,
                added_wage=offer.monthly_salary,
                order=(1, offer.warrior_id),
            )
            for offer in snapshot.pub_offer_list
        ]
        candidate_list += [
            _Candidate(
                decision=BuyFromShop(item_id=offer.item_id),
                price=offer.price,
                added_wage=0,
                order=(2, offer.item_id),
                shop_offer=offer,
            )
            for offer in snapshot.shop_offer_list
        ]
        if snapshot.hall_upgrade is not None:
            candidate_list.append(
                _Candidate(
                    decision=UpgradeHall(new_level=snapshot.hall_upgrade.new_level, price=snapshot.hall_upgrade.price),
                    price=snapshot.hall_upgrade.price,
                    added_wage=0,
                    order=(3, 0),
                    hall_offer=snapshot.hall_upgrade,
                )
            )

        return candidate_list

    @classmethod
    def _score(
        cls,
        *,
        candidate: _Candidate,
        warriors_on_payroll: int,
        held_gear_values: dict[str, list[float]],
    ) -> float:
        if candidate.hall_offer is not None:
            return cls._score_hall(offer=candidate.hall_offer, warriors_on_payroll=warriors_on_payroll)

        if candidate.shop_offer is not None:
            held_values = held_gear_values.get(candidate.shop_offer.slot)
            # Nobody to carry it, or a price of nothing to weigh it against
            if not held_values or candidate.price <= 0:
                return 0.0

            return cls.ITEM_WEIGHT * max(candidate.shop_offer.value - held_values[0], 0.0) / candidate.price

        cost = candidate.price + cls.WAGE_HORIZON_MONTHS * candidate.added_wage
        # A man with neither a price nor a wage costs nothing, and is worth the full weight
        if cost <= 0:
            return float(cls.MAN_WEIGHT)

        return cls.MAN_WEIGHT / cost

    @classmethod
    def _score_hall(cls, *, offer: HallUpgradeOffer, warriors_on_payroll: int) -> float:
        # What the bigger hall pays on top of the standing one, for the men on the payroll by now. Every
        # level above the first is priced, so there is always a price to weigh it against
        added_revenue = Hall.get_building_by_type(building_type=offer.new_level).get_revenue_for_war_band(
            warriors_on_payroll=warriors_on_payroll
        ) - Hall.get_building_by_type(building_type=offer.current_level).get_revenue_for_war_band(
            warriors_on_payroll=warriors_on_payroll
        )

        return cls.BUILDING_WEIGHT * cls.WAGE_HORIZON_MONTHS * added_revenue / offer.price
