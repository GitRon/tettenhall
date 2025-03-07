from django.contrib import admin

from apps.faction.models import Faction
from apps.savegame.models.savegame import Savegame


@admin.register(Savegame)
class SavegameAdmin(admin.ModelAdmin):
    list_display = ("name", "created_by", "created_at", "lastmodified_at", "is_active")
    list_filter = ("created_by", "is_active", "lastmodified_at")

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "player_faction":
            obj_id = request.resolver_match.kwargs.get("object_id")
            if obj_id:
                savegame = Savegame.objects.filter(id=obj_id).first()
                if savegame:
                    kwargs["queryset"] = Faction.objects.filter(savegame=savegame)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
