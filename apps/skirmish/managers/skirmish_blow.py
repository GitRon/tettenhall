from django.db import models
from django.db.models import Q, manager


class SkirmishBlowQuerySet(models.QuerySet):
    def for_savegame(self, *, savegame_id: int):
        return self.filter(skirmish__attacking_faction__savegame_id=savegame_id)

    def for_warrior(self, *, warrior_id: int):
        """
        Every blow this man was part of, from either end of it.

        Two sides on one row is what makes this a query rather than a reverse relation - the stated
        price of recording a blow once instead of twice, and the one place it has to be paid.
        """
        return self.filter(Q(attacker_id=warrior_id) | Q(defender_id=warrior_id))


class SkirmishBlowManager(manager.Manager):
    def create_record(
        self,
        *,
        skirmish,
        round_number: int,
        attacker,
        attacker_action: int,
        defender,
        defender_action: int,
        outcome: int,
        attack,
        defense,
        damage: int = 0,
    ):
        """
        Writes one exchange down, unpacking the two rolls into the columns that survive a restart.
        """
        return self.create(
            skirmish=skirmish,
            round_number=round_number,
            attacker=attacker,
            attacker_action=attacker_action,
            defender=defender,
            defender_action=defender_action,
            outcome=outcome,
            attack_dice=str(attack.roll.notation) if attack.roll else "",
            attack_modifier=attack.roll.notation.modifier if attack.roll else None,
            attack_roll=attack.roll.result if attack.roll else None,
            attack_value=attack.value,
            defense_dice=str(defense.roll.notation),
            defense_modifier=defense.roll.notation.modifier,
            defense_roll=defense.roll.result,
            defense_value=defense.value,
            damage=damage,
        )


SkirmishBlowManager = SkirmishBlowManager.from_queryset(SkirmishBlowQuerySet)
