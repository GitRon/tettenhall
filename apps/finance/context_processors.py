from apps.finance.models import Transaction
from apps.savegame.models.savegame import Savegame
from apps.skirmish.projections.payroll import Payroll


def get_current_balance(request) -> dict:  # noqa: PBR001
    if not request.user.is_authenticated:
        return {}

    # Fetch current savegame record
    current_savegame: Savegame = Savegame.objects.get_current_savegame(user_id=request.user.id)

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
    # The budget is today's balance with no income added. Wages are billed before the hall pays out
    # - "handle_pay_monthly_warrior_salaries_for_new_month" is registered ahead of
    # "handle_earn_money_from_buildings_for_new_month" on FactionMonthPrepared and queuebie drains in
    # order - so this month's income funds next month's wages, not the ones being projected here.
    wage_bill_payroll = Payroll.for_faction(faction=current_savegame.player_faction, budget=current_balance)

    return {"current_balance": current_balance, "wage_bill_payroll": wage_bill_payroll}
