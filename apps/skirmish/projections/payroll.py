from dataclasses import dataclass, field

from apps.skirmish.models import Warrior


@dataclass(kw_only=True)
class Payroll:
    """
    Who a faction can pay out of the silver it has, and who it would have to leave short.

    Built once and read from two ends, which is the whole point of it existing: the salary run bills
    from it when the month turns, and the cost card warns from it beforehand. The split used to sit
    inside "handle_warrior_monthly_salaries", so a warning could only have been a second copy of the
    rule - and a warning naming a different man than the month takes is worse than none.

    Pure: it is handed a roster and a number and reads nothing itself. "for_faction" is the one place
    that touches the database.
    """

    # Cheapest man first, the way "get_payroll_for_faction" hands the roster over. The order is a
    # rule rather than a detail - it decides which man goes without - so this projection takes it as
    # given instead of sorting again and getting to disagree.
    warrior_list: list
    budget: int
    # Read for the desertion projection only, because the leader is the one man who never walks.
    leader_id: int | None

    paid_warrior_list: list = field(init=False, default_factory=list)
    unpaid_warrior_list: list = field(init=False, default_factory=list)

    def __post_init__(self) -> None:
        paid_amount = 0

        for warrior in self.warrior_list:
            # No early exit on the first man the purse cannot cover: the roster is sorted by salary,
            # so everybody after him costs at least as much and fails the same test anyway, and the
            # loop collects them all without a second branch to get wrong
            if paid_amount + warrior.monthly_salary <= self.budget:
                paid_amount += warrior.monthly_salary
                self.paid_warrior_list.append(warrior)
            else:
                self.unpaid_warrior_list.append(warrior)

    @classmethod
    def for_faction(cls, *, faction, budget: int) -> Payroll:
        return cls(
            warrior_list=Warrior.objects.get_payroll_for_faction(faction=faction),
            budget=budget,
            leader_id=faction.leader_id,
        )

    @property
    def paid_amount(self) -> int:
        return sum(warrior.monthly_salary for warrior in self.paid_warrior_list)

    @property
    def missing_amount(self) -> int:
        return sum(warrior.monthly_salary for warrior in self.unpaid_warrior_list)

    @property
    def total_amount(self) -> int:
        return self.paid_amount + self.missing_amount

    @property
    def remaining_amount(self) -> int:
        """
        What is left of the purse once the wages are out of it.

        Goes negative on a shortfall, which is deliberate rather than clamped: the card only shows
        this while the wages are covered, and a floor of zero would read as "nothing left" for a
        faction that is actually in trouble.
        """
        return self.budget - self.total_amount

    @property
    def is_short(self) -> bool:
        return len(self.unpaid_warrior_list) > 0

    @property
    def months_until_desertion(self) -> int:
        """
        How many unpaid months a man takes before he walks, so a template can say the number without
        holding a copy of it.
        """
        return Warrior.UNPAID_MONTHS_UNTIL_DESERTION

    @property
    def deserting_warrior_list(self) -> list:
        """
        The men a shortfall would cost the faction outright rather than only in morale.

        Counted as "one more than he has gone without already", because that is the state
        "handle_punish_unpaid_warrior" reads: the salary run has recorded this month's failure by the
        time it asks. So this is only a projection while nothing has been recorded yet - which is
        exactly when a warning is worth anything.

        The leader is left out for the reason he is left out there: losing him defeats the faction,
        so he sulks indefinitely instead of walking, and a warning that he leaves would be a lie.
        """
        return [
            warrior
            for warrior in self.unpaid_warrior_list
            if warrior.unpaid_months + 1 >= Warrior.UNPAID_MONTHS_UNTIL_DESERTION and warrior.id != self.leader_id
        ]
