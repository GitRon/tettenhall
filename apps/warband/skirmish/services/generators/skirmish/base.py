from apps.warband.skirmish.choices.raid_kind import RaidKindChoices
from apps.warband.skirmish.models.skirmish import Skirmish


class BaseSkirmishGenerator:
    name: str
    warriors_faction_1: list
    warriors_faction_2: list
    month: int
    fortification_strength: int
    raid_kind: int

    def __init__(
        self,
        *,
        name: str,
        warriors_faction_1: list,
        warriors_faction_2: list,
        month: int,
        fortification_strength: int = 0,
        raid_kind: int = RaidKindChoices.STORM_THE_BURH,
    ) -> None:
        super().__init__()

        self.name = name
        self.warriors_faction_1 = warriors_faction_1
        self.warriors_faction_2 = warriors_faction_2
        self.month = month
        self.fortification_strength = fortification_strength
        self.raid_kind = raid_kind

    def process(self) -> Skirmish:
        # Both sides are indexed for their faction below, so an empty one dies on an IndexError that
        # names neither the skirmish nor the side it was missing. The callers guard against it too,
        # but the trap is here, and every future caller would otherwise have to remember it.
        if not self.warriors_faction_1:
            raise RuntimeError(f'Skirmish "{self.name}" has no warriors on the attacking side.')
        if not self.warriors_faction_2:
            raise RuntimeError(f'Skirmish "{self.name}" has no warriors on the defending side.')

        attacking_faction = self.warriors_faction_1[0].faction
        # A march carries the leader whenever he is fit to go
        attacking_leader_id = (
            attacking_faction.leader_id
            if attacking_faction.leader_id in {warrior.id for warrior in self.warriors_faction_1}
            else None
        )

        skirmish = Skirmish.objects.create(
            name=self.name,
            attacking_faction_id=attacking_faction.id,
            attacking_leader_id=attacking_leader_id,
            defending_faction_id=self.warriors_faction_2[0].faction.id,
            month=self.month,
            fortification_strength=self.fortification_strength,
            starting_fortification_strength=self.fortification_strength,
            raid_kind=self.raid_kind,
        )

        skirmish.attacking_warriors.add(*self.warriors_faction_1)
        skirmish.defending_warriors.add(*self.warriors_faction_2)

        return skirmish
