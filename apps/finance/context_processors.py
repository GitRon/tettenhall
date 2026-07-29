from apps.finance.models import Transaction
from apps.savegame.models.savegame import Savegame


def get_current_balance(request) -> dict:  # noqa: PBR001
    if not request.user.is_authenticated:
        return {}

    # Fetch current savegame record
    current_savegame: Savegame = Savegame.objects.get_current_savegame(user_id=request.user.id)

    # A user without an active savegame - a fresh account, for instance - has no balance yet, and
    # neither has one whose player faction is still to be created. The templates only render this
    # inside a "current_savegame" check anyway.
    if current_savegame is None or current_savegame.player_faction_id is None:
        return {}

    current_balance = Transaction.objects.current_balance(faction_id=current_savegame.player_faction_id)

    return {"current_balance": current_balance}
