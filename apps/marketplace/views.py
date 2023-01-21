from django.views import generic

from apps.marketplace.models.marketplace import Marketplace


class MarketplaceView(generic.DetailView):
    model = Marketplace
    template_name = "marketplace/marketplace.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
