from dataclasses import dataclass

from django.db.models import Count

from apps.warband.faction.models.faction import Faction
from apps.warband.skirmish.models import BattleHistory, Skirmish, SkirmishCasualty, Warrior


@dataclass(frozen=True, kw_only=True)
class FallenWarrior:
    """
    One man of the war band who was killed, and the fight that killed him.

    "killed_by" and "death_saga" are empty on a death recorded before either was kept, and the row
    says less rather than something false.
    """

    warrior: Warrior
    skirmish: Skirmish
    killed_by: Warrior | None
    fell_as_a_leader: bool
    death_saga: str
    fights_stood_in: int

    @property
    def killer_side(self) -> Faction:
        """
        The side the killer fought for, read off the fight rather than off the man.

        A killer captured later serves whoever took him, so his own faction would name a side he never
        fought this man for. The fight says it once and for good: the dead man stood on one side of it,
        and the blow came from the other.
        """
        if self.skirmish.attacking_faction_id == self.warrior.faction_id:
            return self.skirmish.defending_faction

        return self.skirmish.attacking_faction


@dataclass(frozen=True, kw_only=True)
class RollOfTheFallen:
    """
    Every man of one faction who was killed, the last to fall first.

    Read from what each fight recorded as it happened rather than from "Warrior.condition": a man only
    dies in a fight, so the casualty rows are the whole list, and they carry the fight he fell in,
    which the warrior row does not.
    """

    fallen_warriors: list[FallenWarrior]

    @classmethod
    def for_faction(cls, *, faction: Faction) -> RollOfTheFallen:
        casualties = list(
            SkirmishCasualty.objects.killed_of_faction(faction_id=faction.id)
            .select_related(
                "warrior__portrait_face",
                "warrior__portrait_hair",
                "warrior__portrait_beard",
                "warrior__hair_colour",
                "warrior__beard_colour",
                "skirmish__attacking_faction",
                "skirmish__defending_faction",
                "killed_by",
            )
            # Distinct per relation: two counts over two joins would otherwise multiply each other
            .annotate(
                attacked_in=Count("warrior__attacking_skirmishes", distinct=True),
                defended_in=Count("warrior__defending_skirmishes", distinct=True),
            )
            # A row is written the moment its man dies, so the newest row is the last man to fall
            .order_by("-id")
        )

        saga_by_death = {
            (line.skirmish_id, line.warrior_id): line.saga
            for line in BattleHistory.objects.filter(
                kind=BattleHistory.KindChoices.KIND_WARRIOR_KILLED,
                warrior_id__in=[casualty.warrior_id for casualty in casualties],
            )
        }

        return cls(
            fallen_warriors=[
                FallenWarrior(
                    warrior=casualty.warrior,
                    skirmish=casualty.skirmish,
                    killed_by=casualty.killed_by,
                    fell_as_a_leader=casualty.fell_as_a_leader,
                    death_saga=saga_by_death.get((casualty.skirmish_id, casualty.warrior_id), ""),
                    fights_stood_in=casualty.attacked_in + casualty.defended_in,
                )
                for casualty in casualties
            ]
        )
