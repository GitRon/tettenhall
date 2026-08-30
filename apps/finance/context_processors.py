from apps.finance.models import Transaction
from apps.savegame.models.savegame import Savegame
from apps.savegame.services.current_savegame import get_current_savegame_for_request
from apps.skirmish.projections.payroll import Payroll


def get_current_balance(request) -> dict:  # noqa: PBR001
    if not request.user.is_authenticated:
        return {}

    # Fetch current savegame record
    current_savegame: Savegame = get_current_savegame_for_request(request=request)

    # A user without an active savegame - a fresh account, for instance - has no balance yet, and
    # neither has one whose player faction is still to be created. Answer with 0 rather than leave
    # the key out: base.html renders the amount behind a "current_savegame" check only, so a missing
    # key puts a silver coin icon followed by nothing into the navbar.
    if current_savegame is None or current_savegame.player_faction_id is None:
        return {"current_balance": 0, "wage_bill_payroll": None}

    current_balance = Transaction.objects.current_balance(faction_id=current_savegame.player_faction_id)

    # The wage bill rides along with the balance rather than living in a context processor of its
    # own, because it is the same purse measured against next month's roster: a second processor
    # would repeat this savegame lookup and this balance query on every authenticated render, and
    # could answer from a different one of the two. The navbar shows them side by side.
    #
    # The budget is today's balance with no income added, which is what the month really bills
    # against: an income returns an event, and the "CreateTransaction" it becomes is queued behind
    # every command the month's events raised, the salary run included. So this month's income funds
    # next month's wages rather than the ones being projected here.
    wage_bill_payroll = Payroll.for_faction(faction=current_savegame.player_faction, budget=current_balance)

    return {"current_balance": current_balance, "wage_bill_payroll": wage_bill_payroll}
