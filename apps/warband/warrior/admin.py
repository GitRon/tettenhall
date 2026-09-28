from ambient_toolbox.admin.model_admins.classes import ReadOnlyAdmin
from django.contrib import admin

from apps.warband.warrior.models.hair_colour import HairColour
from apps.warband.warrior.models.injury import Injury
from apps.warband.warrior.models.injury_type import InjuryType
from apps.warband.warrior.models.portrait_piece import PortraitPiece
from apps.warband.warrior.models.trait import Trait
from apps.warband.warrior.models.trait_type import TraitType


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


@admin.register(TraitType)
class TraitTypeAdmin(ReadOnlyAdmin):
    list_display = ("name", "hook", "group", "attribute", "magnitude", "source")
    list_filter = ("group", "attribute", "source")


@admin.register(Trait)
class TraitAdmin(ReadOnlyAdmin):
    # Read-only because a trait is a record: drawn with the man or earned by a fight, and never lost
    list_display = ("warrior", "type")
    list_filter = ("type", "warrior__faction")


@admin.register(PortraitPiece)
class PortraitPieceAdmin(ReadOnlyAdmin):
    list_display = ("__str__", "image", "left", "top", "width")
    list_filter = ("kind",)


@admin.register(HairColour)
class HairColourAdmin(ReadOnlyAdmin):
    list_display = ("name", "hex")
