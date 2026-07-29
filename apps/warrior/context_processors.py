from apps.savegame.models.savegame import Savegame
from apps.skirmish.models import Warrior


def get_current_amount_warriors(request) -> dict:  # noqa: PBR001
    if not request.user.is_authenticated:
        return {}

    # Fetch current savegame record
    current_savegame: Savegame = Savegame.objects.get_current_savegame(user_id=request.user.id)

    # A user without an active savegame - a fresh account, for instance - has no warriors yet, and
    # a savegame carries no player faction until one has been created for it. Answer with an empty
    # queryset rather than leave the key out: base.html renders the count behind a "current_savegame"
    # check only, so a missing key puts a warrior icon followed by nothing into the navbar.
    if current_savegame is None or current_savegame.player_faction_id is None:
        return {"faction_warriors": Warrior.objects.none()}

    warriors = Warrior.objects.filter_faction(faction_id=current_savegame.player_faction_id).exclude_dead()

    return {"faction_warriors": warriors}
