from django.contrib import admin

from apps.faction.models.culture import Culture
from apps.faction.models.faction import Faction


@admin.register(Culture)
class CultureAdmin(admin.ModelAdmin):
    list_display = ("name", "locale")


@admin.register(Faction)
class FactionAdmin(admin.ModelAdmin):
    list_display = ("name", "culture")
