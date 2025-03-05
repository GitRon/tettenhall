from django.contrib import admin

from apps.training.models.training import Training


@admin.register(Training)
class TrainingAdmin(admin.ModelAdmin):
    list_display = ("category", "faction")
    list_filter = (
        "category",
        "faction__savegame",
    )
