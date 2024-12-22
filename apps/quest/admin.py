from django.contrib import admin

from apps.quest.models.quest import Quest
from apps.quest.models.quest_contract import QuestContract


@admin.register(Quest)
class QuestAdmin(admin.ModelAdmin):
    list_display = ("name", "faction", "difficulty")
    list_filter = ("faction", "difficulty")


@admin.register(QuestContract)
class QuestContractAdmin(admin.ModelAdmin):
    pass
