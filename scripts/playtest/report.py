from dataclasses import asdict, dataclass, field


@dataclass(kw_only=True, frozen=True)
class MonthRecord:
    """Where one savegame stood at the end of one month the harness played."""

    month: int
    player_men: int
    player_silver: int
    # Sorted rather than keyed by faction, so two runs of one seed compare equal whatever ids the
    # database handed out
    rival_men: tuple[int, ...]
    # Sorted the same way, and on its own: it is read for whether any rival runs dry, not for which
    rival_silver: tuple[int, ...]


@dataclass(kw_only=True)
class GameReport:
    """
    What happened in one played savegame.

    Counts what the player did as well as how it went: a step that never fires in a whole game is how a
    harness that has fallen out of step with the views shows up.
    """

    seed: int
    policy: str
    outcome: str = ""
    months_played: int = 0
    # Why the harness stopped a game that was neither decided nor at the month cap
    stop_reason: str | None = None
    fights_won: int = 0
    fights_lost: int = 0
    marches_held_back: int = 0
    marches_unaffordable: int = 0
    occupations: int = 0
    drafted: int = 0
    hired: int = 0
    captives_recruited: int = 0
    player_successions: int = 0
    rival_successions: int = 0
    rival_items_bought: int = 0
    rival_defeat_months: list[int] = field(default_factory=list)
    # (month, building, new level)
    built: list[tuple[int, str, int]] = field(default_factory=list)
    timeline: list[MonthRecord] = field(default_factory=list)

    def as_dict(self) -> dict:
        return asdict(self)
