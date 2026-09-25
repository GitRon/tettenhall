import typing

from django.core.exceptions import ObjectDoesNotExist
from django.db import models

from apps.warband.skirmish.managers.skirmish import SkirmishManager
from apps.warband.skirmish.models.warrior import Warrior

if typing.TYPE_CHECKING:
    from apps.warband.faction.models.faction import Faction


class Skirmish(models.Model):
    name = models.CharField("Name", max_length=100)
    current_round = models.PositiveSmallIntegerField("Current round", default=1)
    # The month the fight belongs to. Nothing recorded it before, and a cap on how often the player
    # may march against the same rival has nowhere else to look: a quest contract knows its month,
    # but an attack carries no contract
    month = models.PositiveSmallIntegerField("Month", default=1)
    # How much wall is still standing between the attackers and the defending faction. Set when the
    # fight is staged and worn down by every assault on it; nothing carries over, so the next march on
    # the same faction meets it whole. Zero is an open field.
    fortification_strength = models.PositiveSmallIntegerField("Fortification strength", default=0)

    # Named for the role each side plays in the fight. Which of them the player holds - if either - is
    # a question for the savegame, so nothing here has to be true of every skirmish ever created
    attacking_faction = models.ForeignKey(
        "warband.Faction",
        verbose_name="Attacking faction",
        related_name="attacking_skirmishes",
        on_delete=models.CASCADE,
    )
    defending_faction = models.ForeignKey(
        "warband.Faction",
        verbose_name="Defending faction",
        related_name="defending_skirmishes",
        on_delete=models.CASCADE,
    )
    victorious_faction = models.ForeignKey(
        "warband.Faction",
        verbose_name="Victorious faction",
        related_name="victorious_skirmishes",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    attacking_warriors = models.ManyToManyField(
        Warrior,
        verbose_name="Attacking warriors",
        related_name="attacking_skirmishes",
    )
    defending_warriors = models.ManyToManyField(
        Warrior,
        verbose_name="Defending warriors",
        related_name="defending_skirmishes",
    )

    objects = SkirmishManager()

    class Meta:
        verbose_name = "Skirmish"
        verbose_name_plural = "Skirmishes"
        default_related_name = "skirmishes"
        # Oldest first, like every other record in this package. A relation traversal wants the
        # order a fight happened in; the one screen that wants the newest at the top - the history
        # on the skirmish list - re-sorts for itself, the way TransactionListView does
        ordering = ("id",)

    def __str__(self) -> str:
        return self.name

    @property
    def rounds_fought(self) -> int:
        """
        How many rounds have been resolved, as opposed to which round is being fought now.

        "current_round" starts at one and is incremented as each round resolves, so it answers "which
        round is this" - right for the header over a fight in progress, and one too many for a column
        counting what a finished fight cost.
        """
        return self.current_round - 1

    @property
    def is_fortified(self) -> bool:
        return self.fortification_strength > 0

    def can_be_assaulted_by(self, *, warrior: Warrior) -> bool:
        """
        Whether this man may spend his round on the wall.

        Only the side that marched has a wall in front of it, and only while any of it stands. Asked of
        the roster rather than of "warrior.faction", which is how every other side question in this
        package is answered: the roster is who fights, whatever the man's faction column says.
        """
        return self.is_fortified and warrior in self.attacking_warriors.all()

    def can_be_rallied_by(self, *, warrior: Warrior) -> bool:
        """
        Whether this man may spend his round steadying his side.

        Only the leader of the faction he fights for in this skirmish. Faction-relative, like the
        walk-out and the dismissal guards, rather than a flag on the man: a rival leader taken prisoner
        and recruited is nobody's leader in the war band that took him, and this answers that without
        recruitment having to clear anything. The side comes off the rosters, as in
        "can_be_assaulted_by".

        The leader ids are asked first, because this runs for every card on the fight page: the two
        factions are cached on this instance after the first card, so a man who leads neither side costs
        no roster query at all.
        """
        if warrior.id not in (self.attacking_faction.leader_id, self.defending_faction.leader_id):
            return False
        if warrior in self.attacking_warriors.all():
            return self.attacking_faction.leader_id == warrior.id
        if warrior in self.defending_warriors.all():
            return self.defending_faction.leader_id == warrior.id
        return False

    def is_defended_by(self, *, warrior: Warrior) -> bool:
        # Membership in ".all()" rather than an "exists()" per call: the round view prefetches both
        # rosters onto the one instance every message of the round carries, so this is asked of every
        # blow without a query
        return warrior in self.defending_warriors.all()

    def quest_reward_for(self, *, victorious_faction: Faction) -> tuple[str | None, int]:
        """
        What this fight pays the side that won it out of the quest it was fought for: the name, and the purse.

        Not every skirmish is somebody's errand - a march on a rival is nobody's - and whether this one
        is belongs to the skirmish rather than to whoever asks. A quest only pays the faction that
        signed the contract, so a rival who takes the field gets the name of what he interrupted and
        none of its money; carrying the purse regardless of the outcome funded the man who beat you out
        of your own quest.

        Answered here rather than in the finance handler that hands the reward over, because reading the
        contract's faction is a query and strict mode forbids one in an event handler.

        The face value, whatever turned out on the day. The purse was already priced against the war
        band the target could field when the quest was pinned to the board - see
        "Quest._priced_for_expected_opposition" - so a thin turnout is a thin contract rather than a
        fraction of a fat one, and the figure the player accepted is the figure he is paid.

        The absence is caught as "ObjectDoesNotExist" rather than as "QuestContract.DoesNotExist",
        which is what it is: naming the contract means importing it, and "QuestContract" reaches back
        through "Warrior" into this very module.
        """
        try:
            quest_contract = self.quest_contract
        except ObjectDoesNotExist:
            return None, 0

        if quest_contract.faction_id != victorious_faction.pk:
            return quest_contract.quest.name, 0

        return quest_contract.quest.name, quest_contract.quest.loot
