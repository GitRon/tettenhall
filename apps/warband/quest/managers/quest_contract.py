from django.db import models
from django.db.models import manager


class QuestContractQuerySet(models.QuerySet):
    def for_player_faction(self, *, faction_id: int):
        return self.filter(faction_id=faction_id)

    def accepted_in(self, *, month: int):
        return self.filter(accepted_in_month=month)

    def still_away(self, *, month: int):
        """Every contract whose men went before "month" and have not come home yet."""
        return self.filter(accepted_in_month__lt=month, resolved_in_month__isnull=True)

    def mark_resolved(self, *, quest_contract, month: int) -> bool:
        """
        Bring a contract home, once.

        A conditional UPDATE rather than a read-modify-save: two month turns overlapping on the same
        savegame both find it still away, and only the one whose write lands may pay it out.
        """
        resolved_rows = self.filter(pk=quest_contract.pk, resolved_in_month__isnull=True).update(
            resolved_in_month=month
        )
        if resolved_rows:
            quest_contract.resolved_in_month = month

        return bool(resolved_rows)


class QuestContractManager(manager.Manager):
    pass


QuestContractManager = QuestContractManager.from_queryset(QuestContractQuerySet)
