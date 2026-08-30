from apps.savegame.services.current_savegame import get_current_savegame_for_request


def current_savegame(request) -> dict:
    return {
        "current_savegame": get_current_savegame_for_request(request=request),
    }
