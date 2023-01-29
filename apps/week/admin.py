from django.contrib import admin

from apps.week.models.player_week_log import PlayerWeekLog


@admin.register(PlayerWeekLog)
class PlayerWeekLogAdmin(admin.ModelAdmin):
    list_display = ("title", "message", "week")
    list_filter = ("week",)
