from django.contrib import admin
from django.db.models import Q, Subquery

from apps.skirmish.models.battle_history import BattleHistory
from apps.skirmish.models.item import Item
from apps.skirmish.models.skirmish import Skirmish
from apps.skirmish.models.warrior import FightAction, Warrior


@admin.register(BattleHistory)
class BattleHistoryAdmin(admin.ModelAdmin):
    list_display = ("message", "skirmish", "created_at")
    list_filter = ("skirmish",)


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = (
        "type",
        "price",
        "value",
        "owner",
        "warrior_weapon",
        "warrior_armor",
    )
    list_filter = (
        "type",
        "owner",
    )


@admin.register(Skirmish)
class SkirmishAdmin(admin.ModelAdmin):
    pass


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
        "weapon",
        "armor",
    )
    list_filter = ("faction", "condition")

    def get_form(self, request, obj=None, change=False, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields["weapon"].queryset = Item.objects.filter(
            type=Item.TypeChoices.TYPE_WEAPON, owner=getattr(obj, "faction", None)
        ).filter(
            ~Q(
                warrior_weapon__in=Subquery(
                    Warrior.objects.exclude(id=getattr(obj, "id", -1)).values_list("id", flat=True)
                )
            )
            | Q(warrior_weapon__isnull=True)
        )
        form.base_fields["armor"].queryset = Item.objects.filter(
            type=Item.TypeChoices.TYPE_ARMOR, owner=getattr(obj, "faction", None)
        ).filter(
            ~Q(
                warrior_armor__in=Subquery(
                    Warrior.objects.exclude(id=getattr(obj, "id", -1)).values_list("id", flat=True)
                )
            )
            | Q(warrior_armor__isnull=True)
        )
        return form
