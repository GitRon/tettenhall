from django.contrib import admin

from apps.quest.models.quest import Quest
from apps.quest.models.quest_contract import QuestContract


@admin.register(Quest)
class QuestAdmin(admin.ModelAdmin):
    list_display = ("name", "target_faction", "difficulty")
    list_filter = ("target_faction", "difficulty")


@admin.register(QuestContract)
class QuestContractAdmin(admin.ModelAdmin):
    pass
