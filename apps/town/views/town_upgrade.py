from django.views import generic

from apps.savegame.models.savegame import Savegame
from apps.town.models import Town


class TownUpgradeView(generic.DetailView):
    model = Town
    template_name = "town/town_upgrade.html"

    def get_object(self, queryset=...):
        return super().get_queryset().first()

    def get_queryset(self):
        current_savegame: Savegame = Savegame.objects.get_current_savegame(user_id=self.request.user.id)
        return Town.objects.for_savegame(savegame_id=current_savegame.id)
