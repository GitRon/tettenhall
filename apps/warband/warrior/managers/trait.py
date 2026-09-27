from django.db import models
from django.db.models import manager


class TraitQuerySet(models.QuerySet):
    def for_warrior(self, *, warrior_id: int):
        return self.filter(warrior_id=warrior_id)


class TraitManager(manager.Manager):
    def create_record(self, *, warrior, trait_type):
        return self.create(warrior=warrior, type=trait_type)


TraitManager = TraitManager.from_queryset(TraitQuerySet)
