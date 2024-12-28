from apps.savegame.models.savegame import Savegame


def current_savegame(request) -> dict:
    return {
        "current_savegame": Savegame.objects.get_current_savegame(user_id=request.user.id),
    }
