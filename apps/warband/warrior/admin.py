from ambient_toolbox.admin.model_admins.classes import ReadOnlyAdmin
from django.contrib import admin

from apps.warband.warrior.models.injury import Injury
from apps.warband.warrior.models.injury_type import InjuryType


@admin.register(InjuryType)
class InjuryTypeAdmin(ReadOnlyAdmin):
    list_display = ("name", "attribute", "magnitude")
    list_filter = ("attribute",)


@admin.register(Injury)
class InjuryAdmin(ReadOnlyAdmin):
    # Read-only because an injury is a record: it is written once by the fight that inflicted it and
    # never mends
    list_display = ("warrior", "type", "inflicted_in_month")
    list_filter = ("type", "warrior__faction")
