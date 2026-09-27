from apps.warband.calendar.months import get_calendar_month
from apps.warband.finance.models import Transaction

UNAFFORDABLE_MARCH_REFUSAL = (
    "Marching {warrior_count} {men} this month costs {march_cost} silver, and you have {balance}."
)


def get_march_cost_refusal(*, faction_id: int, month: int, warrior_count: int) -> str | None:
    """
    Why this faction may not send "warrior_count" men against a rival this month, or None if it may.

    A direct attack and an accepted quest both ask it, because both muster the target's defenders and
    are the same march. Weighed against the purse as it stands, the way a feast is: the march is paid
    the moment it sets out.
    """
    march_cost = get_calendar_month(month=month).get_march_cost(warrior_count=warrior_count)
    if not march_cost:
        return None

    balance = Transaction.objects.current_balance(faction_id=faction_id)
    if balance < march_cost:
        return UNAFFORDABLE_MARCH_REFUSAL.format(
            warrior_count=warrior_count,
            men="man" if warrior_count == 1 else "men",
            march_cost=march_cost,
            balance=balance,
        )

    return None
