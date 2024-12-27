from django.views import generic

from apps.savegame.models.savegame import Savegame


class SavegameListView(generic.ListView):
    model = Savegame
    template_name = "savegame/savegame_list.html"

    def get_queryset(self):
        # TODO: add user login
        # return Savegame.objects.get_for_user(user_id=self.request.user.id)
        return Savegame.objects.all()

    def get_context_data(self, *args, **kwargs):
        # TODO: put this query in a mixin, since we'll need it in MANY views
        context = super().get_context_data(*args, **kwargs)
        # TODO: add user login
        # context["current_savegame"]=Savegame.objects.get_for_user(user_id=self.request.user.id).get_active().first()
        context["current_savegame"] = Savegame.objects.all().get_active().first()
        return context
