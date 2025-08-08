from django.contrib import admin

from apps.town.models import Town


@admin.register(Town)
class TownAdmin(admin.ModelAdmin):
    list_filter = ("faction__savegame",)
