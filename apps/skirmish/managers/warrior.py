from django.db import models
from django.db.models import manager


class WarriorQuerySet(models.QuerySet):
    pass


class WarriorManager(manager.Manager):
    def reduce_current_health(self, obj, damage: int):
        obj.current_health -= damage
        obj.save()

        return obj

    def set_condition(self, obj, condition: int):
        obj.condition = condition
        obj.save()

        return obj

    def take_item_away(self, item):
        """
        Ensure that the given "item" is not being actively used by any warrior
        """
        self.filter(weapon=item).update(weapon=None)
        self.filter(armor=item).update(armor=None)

    def reduce_morale(self, obj, lost_morale: int):
        """
        Drop morale to a minimum of zero
        """
        obj.current_morale = 0 if obj.current_morale - lost_morale < 0 else obj.current_morale - lost_morale
        obj.save()

        return obj

    def increase_morale(self, obj, increased_morale: int):
        """
        Increase morale to a defined maximum
        """
        if obj.current_morale + increased_morale > obj.max_morale:
            obj.current_morale = obj.max_morale
        else:
            obj.current_morale = obj.current_morale + increased_morale
        obj.save()

        return obj

    def increase_experience(self, obj, experience: int):
        """
        Increase experience
        """
        obj.experience += experience
        obj.save()

        return obj


WarriorManager = WarriorManager.from_queryset(WarriorQuerySet)
