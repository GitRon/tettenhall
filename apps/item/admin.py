from ambient_toolbox.admin.model_admins.classes import ReadOnlyAdmin
from django.contrib import admin

from apps.item.models.item import Item
from apps.item.models.item_type import ItemType


@admin.register(ItemType)
class ItemTypeAdmin(ReadOnlyAdmin):
    list_display = ("name", "base_value", "function", "svg_image_name", "is_fallback")


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = (
        "type",
        "condition",
        "price",
        "modifier",
        "owner",
        "warrior_weapon",
        "warrior_armor",
    )
    list_filter = (
        "type",
        "owner",
    )
