from django.contrib import admin
from django.db.models import Q, Subquery

from apps.warband.item.models.item import Item
from apps.warband.item.models.item_type import ItemType
from apps.warband.skirmish.models.battle_history import BattleHistory
from apps.warband.skirmish.models.skirmish import Skirmish
from apps.warband.skirmish.models.skirmish_blow import SkirmishBlow
from apps.warband.skirmish.models.skirmish_casualty import SkirmishCasualty
from apps.warband.skirmish.models.skirmish_spoil import SkirmishSpoil
from apps.warband.skirmish.models.skirmish_warrior_growth import SkirmishWarriorGrowth
from apps.warband.skirmish.models.warrior import Warrior


@admin.register(BattleHistory)
class BattleHistoryAdmin(admin.ModelAdmin):
    list_display = ("message", "skirmish", "created_at")
    list_filter = ("skirmish",)


@admin.register(SkirmishBlow)
class SkirmishBlowAdmin(admin.ModelAdmin):
    list_display = (
        "skirmish",
        "round_number",
        "attacker",
        "attack_item_type",
        "defender",
        "outcome",
        "attack_value",
        "damage",
    )
    list_filter = ("outcome", "attack_item_type", "skirmish")


@admin.register(SkirmishCasualty)
class SkirmishCasualtyAdmin(admin.ModelAdmin):
    list_display = ("skirmish", "warrior", "fate")
    list_filter = ("fate", "skirmish")


@admin.register(SkirmishSpoil)
class SkirmishSpoilAdmin(admin.ModelAdmin):
    list_display = ("skirmish", "faction", "kind", "item", "warrior", "amount")
    list_filter = ("kind", "skirmish")


@admin.register(SkirmishWarriorGrowth)
class SkirmishWarriorGrowthAdmin(admin.ModelAdmin):
    list_display = ("skirmish", "warrior", "faction", "gained_experience", "reached_level")
    list_filter = ("skirmish",)


@admin.register(Skirmish)
class SkirmishAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "current_round",
        "attacking_faction",
        "defending_faction",
        "victorious_faction",
    )
    list_filter = (
        "attacking_faction__savegame",
        "victorious_faction",
    )


@admin.register(Warrior)
class WarriorAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "culture",
        "faction",
        "strength",
        "dexterity",
        "condition",
        "current_health",
        "max_health",
        "weapon",
        "armor",
    )
    list_filter = ("faction", "savegame", "condition")
    search_fields = ("name",)

    def get_form(self, request, obj=None, change=False, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields["weapon"].queryset = Item.objects.filter(
            type__function=ItemType.FunctionChoices.FUNCTION_WEAPON, owner=getattr(obj, "faction", None)
        ).filter(
            ~Q(
                warrior_weapon__in=Subquery(
                    Warrior.objects.exclude(id=getattr(obj, "id", -1)).values_list("id", flat=True)
                )
            )
            | Q(warrior_weapon__isnull=True)
        )
        form.base_fields["armor"].queryset = Item.objects.filter(
            type__function=ItemType.FunctionChoices.FUNCTION_ARMOR, owner=getattr(obj, "faction", None)
        ).filter(
            ~Q(
                warrior_armor__in=Subquery(
                    Warrior.objects.exclude(id=getattr(obj, "id", -1)).values_list("id", flat=True)
                )
            )
            | Q(warrior_armor__isnull=True)
        )
        return form
