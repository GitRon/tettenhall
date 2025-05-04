from apps.savegame.models.savegame import Savegame
from apps.skirmish.models import Warrior


def get_current_amount_warriors(request) -> dict:  # noqa: PBR001
    if not request.user.is_authenticated:
        return {}

    # Fetch current savegame record
    current_savegame: Savegame = Savegame.objects.get_current_savegame(user_id=request.user.id)
    player_faction = current_savegame.player_faction

    warriors = Warrior.objects.filter_faction(faction_id=player_faction.id).exclude_dead()

    return {"faction_warriors": warriors}
