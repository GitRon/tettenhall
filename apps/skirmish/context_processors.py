from apps.savegame.models.savegame import Savegame
from apps.skirmish.models import Skirmish


def get_open_skirmishes(request) -> dict:  # noqa: PBR001
    if not request.user.is_authenticated:
        return {}

    # Fetch current savegame record
    current_savegame: Savegame = Savegame.objects.get_current_savegame(user_id=request.user.id)

    open_skirmishes = Skirmish.objects.for_savegame(savegame_id=current_savegame.id).unresolved()

    return {"open_skirmishes": open_skirmishes}
