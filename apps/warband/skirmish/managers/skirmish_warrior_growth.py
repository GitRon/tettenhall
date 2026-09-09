from django.db import models
from django.db.models import manager


class SkirmishWarriorGrowthQuerySet(models.QuerySet):
    def for_skirmish(self, *, skirmish_id: int):
        return self.filter(skirmish_id=skirmish_id)


class SkirmishWarriorGrowthManager(manager.Manager):
    def record_growth(
        self,
        *,
        skirmish,
        warrior,
        faction,
        gained_experience: int = 0,
        reached_level: int | None = None,
        gained_strength: int = 0,
        gained_dexterity: int = 0,
        gained_max_health: int = 0,
        gained_max_morale: int = 0,
        new_monthly_salary: int | None = None,
    ):
        """
        Folds one grant into the warrior's row for this fight, creating it on the first one.

        The numeric gains accumulate because they arrive in helpings - surviving pays once, every man
        put down pays again - and the report is meant to add them up. The level and the wage are
        stated rather than summed: they are the value the warrior ended the fight at, and a man who
        crosses two thresholds in one fight is at the second one. The grants for a warrior arrive in
        the order they happened, so the last one written is that value.
        """
        growth, _ = self.get_or_create(skirmish=skirmish, warrior=warrior, defaults={"faction": faction})

        growth.gained_experience += gained_experience
        growth.gained_strength += gained_strength
        growth.gained_dexterity += gained_dexterity
        growth.gained_max_health += gained_max_health
        growth.gained_max_morale += gained_max_morale

        if reached_level is not None:
            growth.reached_level = reached_level
        if new_monthly_salary is not None:
            growth.new_monthly_salary = new_monthly_salary

        growth.save()

        return growth


SkirmishWarriorGrowthManager = SkirmishWarriorGrowthManager.from_queryset(SkirmishWarriorGrowthQuerySet)
