from django.contrib import admin

from apps.training.models.training import Training


@admin.register(Training)
class TrainingAdmin(admin.ModelAdmin):
    list_display = ("category",)
    list_filter = ("category",)
