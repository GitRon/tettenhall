from django.http import HttpRequest

from apps.savegame.models.savegame import Savegame

# Attribute the answer is parked on. Underscored because it is this module's business and nothing
# else should read it off the request directly.
_CACHE_ATTRIBUTE = "_current_savegame_cache"


def get_current_savegame_for_request(*, request: HttpRequest) -> Savegame | None:
    """
    The current savegame of the requesting user, resolved once per request.

    Every scoping mixin, most views and four context processors need this, and the context processors
    alone run on every authenticated render - so a single page used to ask the same question seven or
    eight times and get the same row back each time. The answer cannot change within one request, so it
    is worth asking once.

    The cache lives on the request rather than on the view because the context processors have no view
    to hang it on, and they are the callers that made this worth doing.
    """
    if not hasattr(request, _CACHE_ATTRIBUTE):
        setattr(request, _CACHE_ATTRIBUTE, Savegame.objects.get_current_savegame(user_id=request.user.id))

    return getattr(request, _CACHE_ATTRIBUTE)
