from apps.savegame.models.savegame import Savegame
from apps.savegame.services.current_savegame import get_current_savegame_for_request
from apps.skirmish.models import Skirmish


def get_open_skirmishes(request) -> dict:  # noqa: PBR001
    if not request.user.is_authenticated:
        return {}

    # Fetch current savegame record
    current_savegame: Savegame = get_current_savegame_for_request(request=request)

    # A user without an active savegame - a fresh account, for instance - has no skirmishes yet.
    # The templates only render this inside a "current_savegame" check anyway.
    if current_savegame is None:
        return {}

    open_skirmishes = Skirmish.objects.for_savegame(savegame_id=current_savegame.id).unresolved()

    return {"open_skirmishes": open_skirmishes}
