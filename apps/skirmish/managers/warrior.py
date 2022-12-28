from django.db import models
from django.db.models import manager


class WarriorQuestSet(models.QuerySet):
    pass


class WarriorManager(manager.Manager):
    def handle_damage_taken(self, obj, changed_by: int):
        # No damage taken? Nothig to do here.
        if not changed_by:
            return obj

        # Update damage
        obj.current_health -= changed_by

        # Update condition
        if obj.current_health < 0:
            if obj.current_health < obj.max_health * -0.15:
                obj.condition = self.model.ConditionChoices.CONDITION_DEAD
            else:
                obj.condition = self.model.ConditionChoices.CONDITION_UNCONSCIOUS

        obj.save()

        return obj


WarriorManager = WarriorManager.from_queryset(WarriorQuestSet)
