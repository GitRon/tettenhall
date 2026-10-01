from dataclasses import dataclass, field


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
class RivalMonthSnapshot:
    """
    What a rival knows about itself when it decides its month.

    The purse is the one the month opened with: nothing the month earns or spends reaches the ledger
    until every command the monthly handlers raised has run. The wage bill is the whole roster's, read
    off the same [Payroll] the salary run bills from - committed for this month, not yet debited.

    "held_gear_values" is what each man the hand-out may arm carries in each slot, one figure per man,
    an empty slot counting as the fallback's dice. "draft_wage" is what a levy the fyrd has not yet
    rolled is expected to draw.
    """

    fyrd_reserve: int
    purse: int
    wage_bill: int
    band_size: int
    draft_wage: int
    pub_offer_list: list[PubOffer]
    shop_offer_list: list[ShopOffer] = field(default_factory=list)
    held_gear_values: dict[str, list[float]] = field(default_factory=dict)


@dataclass(frozen=True, kw_only=True)
class DraftFromFyrd:
    pass


@dataclass(frozen=True, kw_only=True)
class HireFromPub:
    warrior_id: int


@dataclass(frozen=True, kw_only=True)
class BuyFromShop:
    item_id: int


type RivalDecision = DraftFromFyrd | HireFromPub | BuyFromShop


@dataclass(frozen=True, kw_only=True)
class _Candidate:
    decision: RivalDecision
    price: int
    added_wage: int
    # Settles a tie on score: a draft before a hire before an item, then the lower id
    order: tuple[int, int]
    # The shelf entry behind a purchase, None for a man
    shop_offer: ShopOffer | None = None


class RivalPolicy:
    """
    What a rival does with its month, decided in one place.

    Pure: handed a snapshot, it returns decisions and touches neither the database nor the dice. The
    handler that asks it turns each decision into the same event the player's own button leads to, so a
    rival drafts, hires and buys through the player's commands rather than a second flow beside them.

    **One loop over everything the purse could go on.** Every candidate - the month's one fyrd draft,
    each man in the pub, each item on the shelf - is scored as "weight * need / what it costs", the best
    affordable one is taken, and the loop scores again on the purse, wage bill, band and gear that
    purchase left behind. It stops when nothing scores above MIN_SCORE, and the rest stays in the purse.
    Affordable means the purse still covers the wage bill once over after the purchase, the new man's
    wage included: a man is paid every month, an item once.

    - **A man** is needed while the band is below TARGET_BAND_SIZE and not at all once it is there.
      What he costs is his price plus WAGE_HORIZON_MONTHS of his wage, so a hire is taken from the
      cheapest up.
    - **The pub is only a candidate once the fyrd reserve is empty**, a rule beside the score rather than
      part of it. A rival's income pays more per man than he costs (see [RivalIncome]), so a purse spent
      freely on men pays for the next one: with the pub open beside the draft, a rival grows by two men a
      month instead of one, and over the same 40 seeded savegames the player won none of them against 17
      with the reserve as the brake. TARGET_BAND_SIZE caps how far the band grows, and this caps how fast.
    - **An item** is needed as far as it lifts the weakest man in its slot. The hand-out passes the best
      piece down the line, so buying it leaves the band holding the best of what it held plus the new
      one - the net gain is the new item over the weakest figure, and that figure is what it replaces.
      A man taken earlier in the same month adds nothing to what the band holds: his gear is not known
      until he is.

    The constants are balance numbers, measured with the harness (see "measuring-balance.md").
    """

    TARGET_BAND_SIZE = 12
    WAGE_HORIZON_MONTHS = 6
    MAN_WEIGHT = 1000
    ITEM_WEIGHT = 10
    MIN_SCORE = 0.1

    @classmethod
    def decide(cls, *, snapshot: RivalMonthSnapshot) -> list[RivalDecision]:
        purse = snapshot.purse
        wage_bill = snapshot.wage_bill
        band_size = snapshot.band_size
        # Weakest first, so what a purchase replaces is always the head of the list
        held_gear_values = {slot: sorted(values) for slot, values in snapshot.held_gear_values.items()}
        candidate_list = cls._list_candidates(snapshot=snapshot)
        decision_list: list[RivalDecision] = []

        while True:
            scored_list = [
                (cls._score(candidate=candidate, band_size=band_size, held_gear_values=held_gear_values), candidate)
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

            if best.shop_offer is None:
                band_size += 1
            else:
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
        # The pub only once the reserve is empty - see the class docstring
        if snapshot.fyrd_reserve == 0:
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

        return candidate_list

    @classmethod
    def _score(cls, *, candidate: _Candidate, band_size: int, held_gear_values: dict[str, list[float]]) -> float:
        if candidate.shop_offer is not None:
            held_values = held_gear_values.get(candidate.shop_offer.slot)
            # Nobody to carry it, or a price of nothing to weigh it against
            if not held_values or candidate.price <= 0:
                return 0.0

            return cls.ITEM_WEIGHT * max(candidate.shop_offer.value - held_values[0], 0.0) / candidate.price

        if band_size >= cls.TARGET_BAND_SIZE:
            return 0.0

        cost = candidate.price + cls.WAGE_HORIZON_MONTHS * candidate.added_wage
        # A man with neither a price nor a wage costs nothing, and is worth the full weight
        if cost <= 0:
            return float(cls.MAN_WEIGHT)

        return cls.MAN_WEIGHT / cost
