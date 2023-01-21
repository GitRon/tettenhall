from django.contrib import admin

from apps.item.models.item import Item
from apps.item.models.item_type import ItemType


@admin.register(ItemType)
class ItemTypeAdmin(admin.ModelAdmin):
    list_display = ("function", "svg_image_name")


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
