from django.contrib import admin

from apps.marketplace.models.marketplace import Marketplace


@admin.register(Marketplace)
class MarketplaceAdmin(admin.ModelAdmin):
    pass
