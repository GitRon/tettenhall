from apps.warband.skirmish.models.skirmish import Skirmish


class BaseSkirmishGenerator:
    name: str
    warriors_faction_1: list
    warriors_faction_2: list
    month: int
    fortification_strength: int

    def __init__(
        self,
        *,
        name: str,
        warriors_faction_1: list,
        warriors_faction_2: list,
        month: int,
        fortification_strength: int = 0,
    ) -> None:
        super().__init__()

        self.name = name
        self.warriors_faction_1 = warriors_faction_1
        self.warriors_faction_2 = warriors_faction_2
        self.month = month
        self.fortification_strength = fortification_strength

    def process(self) -> Skirmish:
        # Both sides are indexed for their faction below, so an empty one dies on an IndexError that
        # names neither the skirmish nor the side it was missing. The callers guard against it too,
        # but the trap is here, and every future caller would otherwise have to remember it.
        if not self.warriors_faction_1:
            raise RuntimeError(f'Skirmish "{self.name}" has no warriors on the attacking side.')
        if not self.warriors_faction_2:
            raise RuntimeError(f'Skirmish "{self.name}" has no warriors on the defending side.')

        skirmish = Skirmish.objects.create(
            name=self.name,
            attacking_faction_id=self.warriors_faction_1[0].faction.id,
            defending_faction_id=self.warriors_faction_2[0].faction.id,
            month=self.month,
            fortification_strength=self.fortification_strength,
        )

        skirmish.attacking_warriors.add(*self.warriors_faction_1)
        skirmish.defending_warriors.add(*self.warriors_faction_2)

        return skirmish
