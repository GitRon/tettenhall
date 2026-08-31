from apps.skirmish.models.skirmish import Skirmish
from apps.skirmish.models.warrior import Warrior
from apps.skirmish.projections.skirmish_participant import SkirmishParticipant


class UnknownSkirmishParticipantError(Exception):
    """
    Raised when a posted warrior id names somebody who is not fighting this skirmish.

    A separate exception rather than a return value, because the view answers for it with the same 400
    it already gives every other piece of unusable input - and an empty list is a legitimate result.
    """


class SkirmishParticipantBuilderService:
    """
    Decides who fights this round and with what.

    The player commands one side; the other is the AI's, and its actions are decided here rather than
    read off the request. They used to be posted: the enemy's card rendered the AI's decision into a
    real select carrying the same field name as the player's own, and the Fight! button swept it up -
    so setting every enemy to a defensive stance removed all incoming damage.

    The roster is the authority for *who* fights, not just the AI for *what* they do. Overriding only
    the action would leave a player able to omit an enemy warrior from the post and face fewer
    attackers.
    """

    skirmish: Skirmish
    participants: list[tuple[int, int]]
    player_faction_id: int | None

    def __init__(
        self, *, skirmish: Skirmish, participants: list[tuple[int, int]], player_faction_id: int | None
    ) -> None:
        self.skirmish = skirmish
        self.participants = participants
        self.player_faction_id = player_faction_id

    def _decided_by_the_ai(self, *, roster: list[Warrior]) -> list[SkirmishParticipant]:
        # Only the healthy fight, which is also the only side of the card that ever rendered a control
        return [
            SkirmishParticipant(warrior=warrior, skirmish_action=warrior.decide_skirmish_action()[0])
            for warrior in roster
            if warrior.is_healthy
        ]

    def _posted_by_the_player(self, *, roster: list[Warrior]) -> list[SkirmishParticipant]:
        by_id = {warrior.id: warrior for warrior in roster}

        return [
            SkirmishParticipant(warrior=by_id[warrior_id], skirmish_action=skirmish_action)
            for warrior_id, skirmish_action in self.participants
            if warrior_id in by_id
        ]

    def process(self) -> tuple[list[SkirmishParticipant], list[SkirmishParticipant]]:
        attacking_roster = list(self.skirmish.attacking_warriors.all())
        defending_roster = list(self.skirmish.defending_warriors.all())

        # A posted id belonging to neither side is unusable input, and has to be caught before the
        # side-building below quietly drops it
        known_ids = {warrior.id for warrior in attacking_roster + defending_roster}
        for warrior_id, _skirmish_action in self.participants:
            if warrior_id not in known_ids:
                raise UnknownSkirmishParticipantError

        # The same question SkirmishFightView asks of the same savegame. A savegame without a player
        # faction answers False for both sides rather than guessing at one, which leaves the whole
        # board to the AI - the same answer that view gives when it decides which cards to make
        # editable
        attacker_is_player = self.skirmish.attacking_faction_id == self.player_faction_id
        defender_is_player = self.skirmish.defending_faction_id == self.player_faction_id

        attacking_participants = (
            self._posted_by_the_player(roster=attacking_roster)
            if attacker_is_player
            else self._decided_by_the_ai(roster=attacking_roster)
        )
        defending_participants = (
            self._posted_by_the_player(roster=defending_roster)
            if defender_is_player
            else self._decided_by_the_ai(roster=defending_roster)
        )

        return attacking_participants, defending_participants
