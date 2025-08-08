from django.views import generic

from apps.savegame.models.savegame import Savegame


class TownUpgradeView(generic.TemplateView):
    template_name = "town/town_upgrade.html"

    def get_context_data(self, *, object_list=None, **kwargs) -> dict:
        context = super().get_context_data(object_list=object_list, **kwargs)

        current_savegame: Savegame = Savegame.objects.get_current_savegame(user_id=self.request.user.id)
        context["faction"] = current_savegame.player_faction

        return context
