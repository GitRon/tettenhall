from django.db import models
from django.db.models import manager


class WarriorMilestoneQuerySet(models.QuerySet):
    def for_warrior(self, *, warrior_id: int):
        return self.filter(warrior_id=warrior_id)


class WarriorMilestoneManager(manager.Manager):
    def create_record(
        self,
        *,
        warrior,
        kind: int,
        month: int,
        faction=None,
        skirmish=None,
        other_warrior=None,
        nickname_state: int | None = None,
        joined_way: int | None = None,
    ):
        return self.create(
            warrior=warrior,
            kind=kind,
            month=month,
            faction=faction,
            skirmish=skirmish,
            other_warrior=other_warrior,
            nickname_state=nickname_state,
            joined_way=joined_way,
        )


WarriorMilestoneManager = WarriorMilestoneManager.from_queryset(WarriorMilestoneQuerySet)
