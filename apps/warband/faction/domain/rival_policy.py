from dataclasses import dataclass


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
class RivalMonthSnapshot:
    """
    What a rival knows about itself when it decides its month.

    The purse is the one the month opened with: nothing the month earns or spends reaches the ledger
    until every command the monthly handlers raised has run. The wage bill is the whole roster's, read
    off the same [Payroll] the salary run bills from - committed for this month, not yet debited.
    """

    fyrd_reserve: int
    purse: int
    wage_bill: int
    pub_offer_list: list[PubOffer]


@dataclass(frozen=True, kw_only=True)
class DraftFromFyrd:
    pass


@dataclass(frozen=True, kw_only=True)
class HireFromPub:
    warrior_id: int


type RivalDecision = DraftFromFyrd | HireFromPub


class RivalPolicy:
    """
    What a rival does with its month, decided in one place.

    Pure: handed a snapshot, it returns decisions and touches neither the database nor the dice. The
    handler that asks it turns each decision into the same event the player's own button leads to, so a
    rival drafts and hires through the player's commands rather than a second flow beside them.

    It holds the two decisions a rival takes, and both are greedy, because nothing else competes for
    the purse yet:

    - **The fyrd draft.** One man, whenever the reserve has one and the purse still covers the wage bill
      once over. A draft is free, so what it commits the faction to is his keep, not a price.
    - **The pub hire.** Only once the reserve is empty: the reserve, which refills by a few men a month,
      is the brake #3 balanced a rival's growth on, and "RivalIncome" pays more per man than he costs,
      so a purse spent freely in the pub would pay for the next hire and compound (#387). Then cheapest
      first, which fits the most men into the purse, while the purse less his price still covers the
      wage bill with his wage on it. The purse and the wage bill are kept as running totals across the
      men it takes, since none of the prices reach the ledger before the month's batch has drained.
    """

    @classmethod
    def decide(cls, *, snapshot: RivalMonthSnapshot) -> list[RivalDecision]:
        if snapshot.fyrd_reserve > 0:
            return cls._decide_fyrd_draft(snapshot=snapshot)

        return cls._decide_pub_hires(snapshot=snapshot)

    @staticmethod
    def _decide_fyrd_draft(*, snapshot: RivalMonthSnapshot) -> list[RivalDecision]:
        if snapshot.purse < snapshot.wage_bill:
            return []

        return [DraftFromFyrd()]

    @staticmethod
    def _decide_pub_hires(*, snapshot: RivalMonthSnapshot) -> list[RivalDecision]:
        purse = snapshot.purse
        wage_bill = snapshot.wage_bill
        decision_list: list[RivalDecision] = []

        for offer in sorted(snapshot.pub_offer_list, key=lambda offer: (offer.hiring_price, offer.warrior_id)):
            if purse - offer.hiring_price < wage_bill + offer.monthly_salary:
                continue

            purse -= offer.hiring_price
            wage_bill += offer.monthly_salary
            decision_list.append(HireFromPub(warrior_id=offer.warrior_id))

        return decision_list
