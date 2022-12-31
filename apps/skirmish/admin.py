from django.contrib import admin

from apps.skirmish.models.battle_log import BattleLog
from apps.skirmish.models.faction import Faction
from apps.skirmish.models.item import Item
from apps.skirmish.models.skirmish import Skirmish, SkirmishWarriorRoundAction
from apps.skirmish.models.warrior import Warrior, FightAction


@admin.register(BattleLog)
class BattleLogAdmin(admin.ModelAdmin):
    list_display = ("message", "skirmish", "created_at")
    list_filter = ("skirmish",)


@admin.register(Faction)
class FactionAdmin(admin.ModelAdmin):
    pass


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    pass


class SkirmishWarriorRoundActionInline(admin.TabularInline):
    model = SkirmishWarriorRoundAction


@admin.register(Skirmish)
class SkirmishAdmin(admin.ModelAdmin):
    inlines = (SkirmishWarriorRoundActionInline,)


@admin.register(FightAction)
class FightActionAdmin(admin.ModelAdmin):
    pass


@admin.register(Warrior)
class WarriorAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "faction",
        "dexterity",
        "condition",
        "current_health",
        "max_health",
    )
    list_filter = ("faction", "condition")
