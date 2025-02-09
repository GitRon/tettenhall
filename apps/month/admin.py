from django.contrib import admin

from apps.month.models.player_month_log import PlayerMonthLog


@admin.register(PlayerMonthLog)
class PlayerMonthLogAdmin(admin.ModelAdmin):
    list_display = ("title", "month")
    list_filter = ("month",)
