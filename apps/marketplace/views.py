from django.views import generic

from apps.marketplace.models.marketplace import Marketplace
from apps.savegame.models.savegame import Savegame


class MarketplaceView(generic.DetailView):
    model = Marketplace
    template_name = "marketplace/marketplace.html"

    def get_queryset(self):
        current_savegame: Savegame = Savegame.objects.get_current_savegame(user_id=self.request.user.id)
        return super().get_queryset().for_savegame(savegame_id=current_savegame)
