from dataclasses import dataclass

from apps.faction.models.faction import Faction
from apps.item.models.item import Item
from apps.skirmish.models import Skirmish, SkirmishCasualty, SkirmishSpoil, SkirmishWarriorGrowth, Warrior


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
    # Every man either side lost, for the same reason the spoils are taken whole: whose casualty a
    # fallen man is, and whether he is a loss or a prisoner gained, is this projection's job
    casualty_list: list
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
            casualty_list=list(
                SkirmishCasualty.objects.for_skirmish(skirmish_id=skirmish.id).select_related("warrior")
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
        """
        What the fight actually handed the faction, which is not everything that came its way.

        Its own dead are stripped too, and the loot goes to the victor - so on a won fight a man's
        own sword and purse arrive here as gains off a warrior who is on the roster. That is the
        stash getting its kit back, not booty, and filing it under gains let a fight that killed one
        of five men read as a profit. It is not a loss either: nobody walked off with it. The man
        himself is reported as a casualty, which is the thing that actually happened.
        """
        return [
            spoil
            for spoil in self.spoil_list
            if spoil.kind == kind
            and spoil.faction_id == self.faction.id
            and spoil.warrior_id not in self.own_warrior_ids
        ]

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

    def _own_casualties_with_fate(self, *, fate: int) -> list:
        return [
            casualty
            for casualty in self.casualty_list
            if casualty.fate == fate and casualty.warrior_id in self.own_warrior_ids
        ]

    def _enemy_casualties_with_fate(self, *, fate: int) -> list:
        return [
            casualty
            for casualty in self.casualty_list
            if casualty.fate == fate and casualty.warrior_id not in self.own_warrior_ids
        ]

    @property
    def own_casualties(self) -> list:
        """
        The men the fight cost, each carrying which of the three things happened to him.

        Read against the rosters rather than against the warriors' own factions, because a man taken
        prisoner in this very fight belongs to the side that beat him by the time this renders - he
        is exactly the casualty the player most needs told about, and reading his faction would hand
        him to the enemy's column.

        The fate is what separates a man who is gone from one who is merely down: the winner's
        unconscious keep their gear and their place, and a report that called them losses would be
        wrong about them every time.
        """
        return [
            casualty
            for casualty in self.casualty_list
            if casualty.warrior_id in self.own_warrior_ids and casualty.fate != SkirmishCasualty.FateChoices.FATE_FLED
        ]

    @property
    def own_routed(self) -> list:
        """
        The men whose nerve went, kept apart from the casualties on purpose.

        Fleeing costs the player nothing - the man keeps his kit and rallies next month - so naming
        him among the fallen would report a loss he did not take. He is here because five men
        marching and three fighting is otherwise unexplained.
        """
        return self._own_casualties_with_fate(fate=SkirmishCasualty.FateChoices.FATE_FLED)

    @property
    def prisoners_taken(self) -> list:
        """
        Enemy men the fight handed the faction, named rather than counted.

        A prisoner is the one outcome of a fight that keeps paying - he can be held, healed and given
        back - and the player otherwise finds him only by opening a screen he has no reason to open.
        """
        return self._enemy_casualties_with_fate(fate=SkirmishCasualty.FateChoices.FATE_CAPTURED)

    @property
    def enemy_killed_count(self) -> int:
        """
        Counted, not named. Recording every enemy name costs nothing, but a report listing eight of
        them buries the two of the player's own that he cannot get back.
        """
        return len(self._enemy_casualties_with_fate(fate=SkirmishCasualty.FateChoices.FATE_KILLED))

    @property
    def enemy_downed_count(self) -> int:
        """
        Enemies left unconscious and not taken, which is what a fight the player lost leaves behind:
        the winning side's casualties keep themselves.
        """
        return len(self._enemy_casualties_with_fate(fate=SkirmishCasualty.FateChoices.FATE_INCAPACITATED))

    @property
    def has_anything_to_report(self) -> bool:
        """
        Whether the fight yielded anything at all.

        A won fight that took nothing off a poor enemy is a real outcome, and the panel says so in
        one sentence rather than showing three empty headings. A fight that cost a man is never one
        of those, however bare his pockets were - which is the case that used to print "the fight
        yielded nothing" over a dead warrior.
        """
        return (
            bool(
                self.items_won
                or self.items_lost
                or self.growth_list
                or self.own_casualties
                or self.own_routed
                or self.prisoners_taken
            )
            or (self.silver_won + self.silver_lost) > 0
            or (self.enemy_killed_count + self.enemy_downed_count) > 0
        )
