from django.views import generic

from apps.savegame.mixins import CurrentSavegameMixin
from apps.savegame.models.savegame import Savegame


class SavegameListView(CurrentSavegameMixin, generic.ListView):
    model = Savegame
    template_name = "savegame/savegame_list.html"

    # TODO: login logic
    # TODO: create new savegame form (town name, faction name etc.)

    def get_queryset(self):
        # TODO: add user login
        # return Savegame.objects.get_for_user(user_id=self.request.user.id)
        return Savegame.objects.all()
