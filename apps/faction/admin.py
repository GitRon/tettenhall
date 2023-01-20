from django.contrib import admin

from apps.faction.models.faction import Faction


@admin.register(Faction)
class FactionAdmin(admin.ModelAdmin):
    list_display = ("name", "locale")
