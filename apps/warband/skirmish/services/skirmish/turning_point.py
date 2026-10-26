import typing

from apps.warband.skirmish.choices.turning_point import TurningPointChoices
from apps.warband.skirmish.domain.turning_point import TurningPointFinding, is_in_trouble, most_important
from apps.warband.skirmish.models.warrior import Warrior

if typing.TYPE_CHECKING:
    from apps.warband.faction.models.faction import Faction
    from apps.warband.skirmish.models import Skirmish


class TurningPointService:
    """
    Reads a round that has just been fought for the moments that stop the fight and wait for the player.

    Asked after the round rather than before it, because whom a man faces is only drawn while the round
    is resolved - there is nothing to read before it.
    """

    skirmish: Skirmish
    fielded_warriors: list[Warrior]
    player_faction: Faction | None

    def __init__(self, *, skirmish: Skirmish, fielded_warriors: list[Warrior], player_faction: Faction | None):
        self.skirmish = skirmish
        self.fielded_warriors = fielded_warriors
        self.player_faction = player_faction

    def _leader_in_trouble(self, *, faction: Faction, roster_ids: set[int], warriors_by_id: dict) -> bool:
        """
        Whether this side's leader is on its roster, still on his feet, and down to under half his health.

        A leader who went down this round is not in trouble any more, he is down - and the player hears
        about that as a man down rather than being offered to pull back a man who is no longer standing.
        """
        leader = warriors_by_id.get(faction.leader_id) if faction.leader_id in roster_ids else None
        if leader is None or not leader.is_healthy:
            return False

        return is_in_trouble(current_health=leader.current_health, max_health=leader.max_health)

    def process(self) -> TurningPointFinding | None:
        """
        What the round left for the player, or None when he has no side in this fight to be asked about.
        """
        if self.player_faction is None or self.player_faction.id not in (
            self.skirmish.attacking_faction_id,
            self.skirmish.defending_faction_id,
        ):
            return None

        attacking_ids = set(self.skirmish.attacking_warriors.values_list("id", flat=True))
        defending_ids = set(self.skirmish.defending_warriors.values_list("id", flat=True))
        # Read again rather than off the instances the round was drawn with, which still say what each
        # man was when it began
        warriors_by_id = Warrior.objects.filter(id__in=attacking_ids | defending_ids).in_bulk()

        attacking_leader_in_trouble = self._leader_in_trouble(
            faction=self.skirmish.attacking_faction, roster_ids=attacking_ids, warriors_by_id=warriors_by_id
        )
        defending_leader_in_trouble = self._leader_in_trouble(
            faction=self.skirmish.defending_faction, roster_ids=defending_ids, warriors_by_id=warriors_by_id
        )

        if self.player_faction.id == self.skirmish.attacking_faction_id:
            player_ids = attacking_ids
            player_leader_is_new_in_trouble = (
                attacking_leader_in_trouble and not self.skirmish.attacking_leader_was_in_trouble
            )
            enemy_leader_is_new_in_trouble = (
                defending_leader_in_trouble and not self.skirmish.defending_leader_was_in_trouble
            )
        else:
            player_ids = defending_ids
            player_leader_is_new_in_trouble = (
                defending_leader_in_trouble and not self.skirmish.defending_leader_was_in_trouble
            )
            enemy_leader_is_new_in_trouble = (
                attacking_leader_in_trouble and not self.skirmish.attacking_leader_was_in_trouble
            )

        # Everyone of the player's who stood when the round began and does not any more: knocked out,
        # killed or fled. All of them share one stop
        fallen = [
            warriors_by_id[warrior.id]
            for warrior in self.fielded_warriors
            if warrior.id in player_ids and not warriors_by_id[warrior.id].is_healthy
        ]

        turning_points = []
        if player_leader_is_new_in_trouble:
            turning_points.append(TurningPointChoices.LEADER_THREATENED)
        if fallen:
            turning_points.append(TurningPointChoices.MAN_DOWN)
        if enemy_leader_is_new_in_trouble:
            turning_points.append(TurningPointChoices.ENEMY_LEADER_EXPOSED)
        turning_point = most_important(turning_points=turning_points)

        return TurningPointFinding(
            turning_point=turning_point,
            warriors=fallen if turning_point == TurningPointChoices.MAN_DOWN else [],
            attacking_leader_in_trouble=attacking_leader_in_trouble,
            defending_leader_in_trouble=defending_leader_in_trouble,
        )
