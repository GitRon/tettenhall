from django.contrib import admin

from apps.warband.incident.models.pending_incident import PendingIncident


@admin.register(PendingIncident)
class PendingIncidentAdmin(admin.ModelAdmin):
    list_display = ("title", "incident", "faction", "month")
    list_filter = ("incident", "month")
