from ambient_toolbox.admin.model_admins.classes import ReadOnlyAdmin
from django.contrib import admin

from apps.warband.quest.models.quest import Quest
from apps.warband.quest.models.quest_contract import QuestContract
from apps.warband.quest.models.quest_name import QuestName


@admin.register(Quest)
class QuestAdmin(admin.ModelAdmin):
    list_display = ("name", "target_faction", "difficulty")
    list_filter = ("target_faction", "difficulty")


@admin.register(QuestContract)
class QuestContractAdmin(admin.ModelAdmin):
    pass


@admin.register(QuestName)
class QuestNameAdmin(ReadOnlyAdmin):
    list_display = ("name",)
