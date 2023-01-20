from django.contrib import admin

from apps.finance.models.transaction import Transaction


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ("reason", "amount", "faction")
    list_filter = ("faction",)
