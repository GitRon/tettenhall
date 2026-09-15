from django.db import models
from django.db.models import manager


class InjuryQuerySet(models.QuerySet):
    def for_warrior(self, *, warrior_id: int):
        return self.filter(warrior_id=warrior_id)


class InjuryManager(manager.Manager):
    def create_record(self, *, warrior, injury_type, month: int):
        return self.create(warrior=warrior, type=injury_type, inflicted_in_month=month)


InjuryManager = InjuryManager.from_queryset(InjuryQuerySet)
