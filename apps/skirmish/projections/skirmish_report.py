from dataclasses import dataclass

from apps.faction.models.faction import Faction
from apps.item.models.item import Item
from apps.skirmish.models import Skirmish, SkirmishSpoil, SkirmishWarriorGrowth, Warrior


@dataclass(kw_only=True)
class SpoiledItem:
    """
    A piece of gear the fight moved, and whether picking it up is worth doing anything about.
    """

    item: Item
    taken_from: Warrior | None
    # Measured against the best of its kind the faction's men are actually wearing, which is the
    # question the numbers on the item exist to answer and the one the game never asked out loud
    is_upgrade: bool


@dataclass(kw_only=True)
class SkirmishReport:
    """
    What a finished fight got one faction, and what it cost it.

    Pure: it is handed the fight's recorded spoils and reads nothing itself. "for_skirmish" is the
    one place that touches the database.

    A report has a side, which the battle log never had to have: the log is written for both factions
    in one voice, so the player reads his own men being stripped in the same sentence shape as the
    enemy's. Every list below is answered from "faction"'s point of view.
    """

    skirmish: Skirmish
    faction: Faction
    # Every spoil of the fight, both sides. Which of them are gains and which are losses is this
    # projection's whole job, so it takes the lot rather than a pre-picked half
    spoil_list: list
    # Already narrowed to the faction's own men: growth only ever reads as a gain, and the enemy
    # getting better at fighting is not something a report of your own battle tells you
    growth_list: list
    # Who this faction fielded, which is what says whose gear the other side walked off with. Read
    # from the rosters rather than from the warriors' own factions, because a man captured in this
    # very fight belongs to the side that beat him by the time the report is rendered
    own_warrior_ids: set
    best_worn_weapon_value: float
    best_worn_armor_value: float

    @classmethod
    def for_skirmish(cls, *, skirmish, faction) -> SkirmishReport:
        if skirmish.attacking_faction_id == faction.id:
            own_warriors = skirmish.attacking_warriors
        else:
            own_warriors = skirmish.defending_warriors

        return cls(
            skirmish=skirmish,
            faction=faction,
            spoil_list=list(
                SkirmishSpoil.objects.for_skirmish(skirmish_id=skirmish.id).select_related(
                    "item__type", "warrior", "faction"
                )
            ),
            growth_list=list(
                SkirmishWarriorGrowth.objects.for_skirmish(skirmish_id=skirmish.id)
                .filter(faction_id=faction.id)
                .select_related("warrior")
            ),
            own_warrior_ids=set(own_warriors.values_list("id", flat=True)),
            # Worn rather than merely owned, which is the comparison worth making: the sword that has
            # just been taken sits in the stash unworn, so it is measured against what one of the
            # faction's men is actually swinging instead of against itself
            best_worn_weapon_value=cls._best_expectancy_value(
                item_list=Item.objects.filter(owner_id=faction.id, warrior_weapon__isnull=False).select_related("type")
            ),
            best_worn_armor_value=cls._best_expectancy_value(
                item_list=Item.objects.filter(owner_id=faction.id, warrior_armor__isnull=False).select_related("type")
            ),
        )

    @staticmethod
    def _best_expectancy_value(*, item_list) -> float:
        return max((item.expectancy_value for item in item_list), default=0.0)

    @property
    def is_victory(self) -> bool:
        return self.skirmish.victorious_faction_id == self.faction.id

    def _gained(self, *, kind: int) -> list:
        return [spoil for spoil in self.spoil_list if spoil.kind == kind and spoil.faction_id == self.faction.id]

    def _lost(self, *, kind: int) -> list:
        return [
            spoil
            for spoil in self.spoil_list
            if spoil.kind == kind and spoil.faction_id != self.faction.id and spoil.warrior_id in self.own_warrior_ids
        ]

    def _is_upgrade(self, *, item: Item) -> bool:
        if item.is_weapon:
            return item.expectancy_value > self.best_worn_weapon_value

        return item.expectancy_value > self.best_worn_armor_value

    @property
    def items_won(self) -> list[SpoiledItem]:
        return [
            SpoiledItem(item=spoil.item, taken_from=spoil.warrior, is_upgrade=self._is_upgrade(item=spoil.item))
            for spoil in self._gained(kind=SkirmishSpoil.KindChoices.KIND_ITEM_TAKEN)
        ]

    @property
    def items_lost(self) -> list:
        return self._lost(kind=SkirmishSpoil.KindChoices.KIND_ITEM_TAKEN)

    @property
    def silver_looted(self) -> int:
        return sum(spoil.amount for spoil in self._gained(kind=SkirmishSpoil.KindChoices.KIND_SILVER_LOOTED))

    @property
    def silver_lost(self) -> int:
        return sum(spoil.amount for spoil in self._lost(kind=SkirmishSpoil.KindChoices.KIND_SILVER_LOOTED))

    @property
    def quest_reward(self) -> int:
        return sum(spoil.amount for spoil in self._gained(kind=SkirmishSpoil.KindChoices.KIND_QUEST_REWARD))

    @property
    def quest_name(self) -> str:
        return next((spoil.description for spoil in self._gained(kind=SkirmishSpoil.KindChoices.KIND_QUEST_REWARD)), "")

    @property
    def silver_won(self) -> int:
        return self.silver_looted + self.quest_reward

    @property
    def has_anything_to_report(self) -> bool:
        """
        Whether the fight yielded anything at all.

        A won fight that took nothing off a poor enemy is a real outcome, and the panel says so in
        one sentence rather than showing three empty headings.
        """
        return bool(self.items_won or self.items_lost or self.growth_list) or (self.silver_won + self.silver_lost) > 0
