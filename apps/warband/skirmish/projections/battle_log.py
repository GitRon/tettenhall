from dataclasses import dataclass

from apps.warband.skirmish.models import BattleHistory


@dataclass(frozen=True, kw_only=True)
class BattleLogRound:
    """
    One round of a fight, and every line the game wrote while it was being fought.

    The lines stay in the order they were written. Reversing inside a round would put a man on the
    ground above the blow that felled him, which is the one thing a blow-by-blow may not do.
    """

    number: int
    lines: list[BattleHistory]

    @property
    def saga_lines(self) -> list[BattleHistory]:
        """
        The round as the Saga tells it: only the lines that carry a saga sentence, in the same order.
        """
        return [line for line in self.lines if line.saga]


@dataclass(frozen=True, kw_only=True)
class BattleLog:
    """
    A fight's log, cut into rounds and stacked with the newest on top.

    A long fight is a hundred lines of which the player wants the last ten, and reading it meant
    scrolling past every round he had already watched. Only the stack is reversed, never a round's
    own contents - see "BattleLogRound".

    Pure: it is handed the lines and reads nothing itself. The one view that renders the log already
    holds a savegame-scoped queryset of it, and a projection fetching its own would be a second,
    unscoped way to the same rows - the leak [savegame scoping](docs/patterns/savegame-scoping.md)
    exists to prevent.
    """

    rounds: list[BattleLogRound]

    @property
    def has_saga(self) -> bool:
        """
        Whether any line of the fight carries a saga sentence.

        A fight that has lines and none of them told is one recorded before the saga was kept, and its
        Saga tab says so instead of standing empty.
        """
        return any(log_round.saga_lines for log_round in self.rounds)

    @classmethod
    def from_lines(cls, *, lines: list[BattleHistory]) -> BattleLog:
        """
        Cuts a fight's lines, in the order they were written, into rounds.

        A round's boundary line closes it, so the cut comes after it rather than before. What follows
        the last boundary is the fight's own conclusion and not a round nobody fought: the victor,
        the experience and the loot are all written off "SkirmishFinished", which is raised downstream
        of the last "RoundFinished". It belongs to the round that ended the fight, so it is folded in
        there.

        The number is the block's position, which holds because rounds are fought in order and each
        one writes exactly one boundary. A log with no boundary in it yet is round one - the same
        rule, counted from a fight that has not closed a round.
        """
        blocks: list[list[BattleHistory]] = []
        current_block: list[BattleHistory] = []

        for line in lines:
            if line.is_round_boundary:
                # Dropped rather than kept: the whole of what it says is the number the heading over
                # the block already carries, and "Round 3" above "Round 3 finished." is noise in the
                # panel this stacking exists to make readable.
                blocks.append(current_block)
                current_block = []
            else:
                current_block.append(line)

        if current_block:
            if blocks:
                blocks[-1] += current_block
            else:
                blocks.append(current_block)

        return cls(
            rounds=[BattleLogRound(number=number, lines=block) for number, block in enumerate(blocks, start=1)][::-1]
        )
