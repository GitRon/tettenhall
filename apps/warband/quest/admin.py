from django.contrib import admin

from apps.warband.quest.models.quest import Quest
from apps.warband.quest.models.quest_contract import QuestContract


@admin.register(Quest)
class QuestAdmin(admin.ModelAdmin):
    list_display = ("title", "faction", "month")
    list_filter = ("faction",)


@admin.register(QuestContract)
class QuestContractAdmin(admin.ModelAdmin):
    list_display = ("title", "faction", "accepted_in_month", "resolved_in_month")
    list_filter = ("faction",)
