from ambient_toolbox.admin.model_admins.classes import ReadOnlyAdmin
from django.contrib import admin

from apps.faction.models.culture import Culture
from apps.faction.models.faction import Faction


@admin.register(Culture)
class CultureAdmin(ReadOnlyAdmin):
    list_display = ("name", "locale")


@admin.register(Faction)
class FactionAdmin(admin.ModelAdmin):
    list_display = ("name", "culture", "savegame")
    list_filter = ("savegame",)
