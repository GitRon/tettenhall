from dataclasses import dataclass

from apps.warband.skirmish.choices.fight_directive import FightDirectiveChoices
from apps.warband.skirmish.choices.turning_point import TurningPointChoices
from apps.warband.skirmish.models.skirmish import Skirmish
from apps.warband.skirmish.models.warrior import Warrior
from apps.warband.skirmish.services.skirmish.fight_directive import get_offered_directives


@dataclass(kw_only=True)
class PendingTurningPoint:
    """
    The stop a fight is waiting at, as the player is shown it: what happened, and what he may answer.
    """

    turning_point: TurningPointChoices
    # The answers he may give besides fighting on and taking command, which every stop offers
    directives: list[FightDirectiveChoices]
    # The men a "man down" stop names, and nobody for the other two
    fallen: list[Warrior]
    # The leader the stop is about: the player's own when he is threatened, the enemy's when he is
    # exposed, and nobody for a man down
    leader: Warrior | None

    # Each stop is told in its own words, and a template cannot compare against a choice
    @property
    def is_leader_threatened(self) -> bool:
        return self.turning_point == TurningPointChoices.LEADER_THREATENED

    @property
    def is_man_down(self) -> bool:
        return self.turning_point == TurningPointChoices.MAN_DOWN

    @classmethod
    def for_skirmish(cls, *, skirmish: Skirmish, player_faction_id: int | None) -> PendingTurningPoint | None:
        """
        The stop waiting for the player in this fight, or None when there is none to show.

        A decided fight has no next round to answer, whatever the last one left behind.
        """
        if skirmish.turning_point is None or skirmish.victorious_faction_id is not None:
            return None

        if skirmish.attacking_faction_id == player_faction_id:
            player_roster, player_faction, enemy_faction = (
                skirmish.attacking_warriors.all(),
                skirmish.attacking_faction,
                skirmish.defending_faction,
            )
        elif skirmish.defending_faction_id == player_faction_id:
            player_roster, player_faction, enemy_faction = (
                skirmish.defending_warriors.all(),
                skirmish.defending_faction,
                skirmish.attacking_faction,
            )
        else:
            return None

        turning_point = TurningPointChoices(skirmish.turning_point)
        leader = {
            TurningPointChoices.LEADER_THREATENED: player_faction.leader,
            TurningPointChoices.ENEMY_LEADER_EXPOSED: enemy_faction.leader,
        }.get(turning_point)

        return cls(
            turning_point=turning_point,
            directives=get_offered_directives(
                turning_point=turning_point, skirmish=skirmish, roster=list(player_roster.select_related("faction"))
            ),
            fallen=list(skirmish.turning_point_warriors.select_related("faction")),
            leader=leader,
        )
