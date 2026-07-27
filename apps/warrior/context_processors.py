from apps.savegame.models.savegame import Savegame
from apps.skirmish.models import Warrior


def get_current_amount_warriors(request) -> dict:  # noqa: PBR001
    if not request.user.is_authenticated:
        return {}

    # Fetch current savegame record
    current_savegame: Savegame = Savegame.objects.get_current_savegame(user_id=request.user.id)

    # A user without an active savegame - a fresh account, for instance - has no warriors yet, and
    # a savegame carries no player faction until one has been created for it. The templates only
    # render this inside a "current_savegame" check anyway.
    if current_savegame is None or current_savegame.player_faction is None:
        return {}

    warriors = Warrior.objects.filter_faction(faction_id=current_savegame.player_faction_id).exclude_dead()

    return {"faction_warriors": warriors}
