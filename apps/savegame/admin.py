from django.contrib import admin

from apps.savegame.models.savegame import Savegame


@admin.register(Savegame)
class SavegameAdmin(admin.ModelAdmin):
    list_display = ("name", "created_by", "created_at", "lastmodified_at", "is_active")
    list_filter = ("created_by", "is_active", "lastmodified_at")
