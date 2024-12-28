from apps.savegame.models.savegame import Savegame


class CurrentSavegameMixin:
    def get_context_data(self, *args, **kwargs) -> dict:
        # Some views don't have this method
        try:
            context = super().get_context_data(*args, **kwargs)
        except AttributeError:
            context = {}
        # TODO: add user login
        # context["current_savegame"]=Savegame.objects.get_current_savegame(user_id=self.request.user.id)
        context["current_savegame"] = Savegame.objects.all().get_active().first()
        return context
