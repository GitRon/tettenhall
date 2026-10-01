import random
from dataclasses import dataclass, replace

from django.contrib.auth.models import User
from queuebie.runner import handle_message

from apps.warband.faction.models.culture import Culture
from apps.warband.faction.models.faction import Faction
from apps.warband.finance.models import Transaction
from apps.warband.month.messages.commands.month import PrepareMonth
from apps.warband.savegame.messages.commands.savegame import CreateNewSavegame
from apps.warband.savegame.models.savegame import Savegame
from apps.warband.skirmish.models.skirmish import Skirmish
from apps.warband.skirmish.models.warrior import Warrior
from scripts.playtest.player import PlayerTurn
from scripts.playtest.policy import PlayerPolicy
from scripts.playtest.report import GameReport, MonthRecord

STOP_MONTH_BLOCKED = "month blocked by an unresolved skirmish"


def play_savegame(*, seed: int, policy: PlayerPolicy, month_cap: int, user: User) -> GameReport:
    """
    Starts a savegame the way the new-game form does and plays it until it is decided or reaches the cap.

    Everything the game rolls comes off the module-level "random", so seeding it makes the savegame
    repeat exactly. The harness's own choices - the culture, the tie between two targets - come off a
    generator of their own, seeded alike, so they do not shift the game's draws.
    """
    random.seed(seed)
    rng = random.Random(seed)

    handle_message(
        CreateNewSavegame(
            town_name=f"Town {seed}",
            faction_name=f"Band {seed}",
            faction_culture_id=rng.choice(sorted(Culture.objects.values_list("id", flat=True))),
            created_by_id=user.id,
        )
    )
    savegame = Savegame.objects.filter(created_by=user).latest("id")

    return play_months(
        savegame=savegame, policy=policy, rng=rng, month_cap=month_cap, report=GameReport(seed=seed, policy=policy.name)
    )


def play_months(
    *, savegame: Savegame, policy: PlayerPolicy, rng: random.Random, month_cap: int, report: GameReport
) -> GameReport:
    """
    Plays the player's month and then finishes it, as the End Month button does, until the game stops.

    The game stops when it is decided, when it reaches the cap, or when the harness cannot go on - a
    fight nobody can finish, or a month the game refuses to finish. The last two are said in
    "stop_reason" rather than looped on.
    """
    standings = _standings(savegame=savegame)

    while not savegame.is_over and report.months_played < month_cap:
        turn = PlayerTurn(savegame=savegame, policy=policy, rng=rng, report=report)
        stop_reason = turn.play()
        player_id = savegame.player_faction_id
        standings[player_id] = replace(standings[player_id], roster_ids=turn.roster_ids_at_march)
        savegame = _reload(savegame=savegame)

        if stop_reason is None and not savegame.is_over:
            # The refusal "FinishMonthView" answers with, asked before the month is sent
            if Skirmish.objects.unresolved().for_savegame(savegame_id=savegame.id).exists():
                stop_reason = STOP_MONTH_BLOCKED
            else:
                handle_message(PrepareMonth(savegame=savegame, month=savegame.current_month))
                savegame = _reload(savegame=savegame)

        report.months_played += 1
        report.timeline.append(_record_month(savegame=savegame, month=report.months_played))
        standings = _count_successions(savegame=savegame, before=standings, report=report)

        if stop_reason is not None:
            report.stop_reason = stop_reason
            break

    report.outcome = savegame.get_outcome_display()
    report.rival_items_bought = _count_rival_purchases(savegame=savegame)
    return report


def _reload(*, savegame: Savegame) -> Savegame:
    return Savegame.objects.select_related("player_faction").get(pk=savegame.pk)


@dataclass(frozen=True, kw_only=True)
class Standing:
    """
    Where one faction stood at the end of a month, as far as its seat is concerned.

    The roster is kept so that a new leader can be told apart: a man who was on it is the next in line,
    and a man who was not was raised from the fyrd. A rival's roster only moves in the month run, after
    every fight, so last month's is the one to compare against. The player's moves in his own turn before
    the march, so "play_months" swaps in the roster he set out with.
    "first_fall_month" is the month the faction first lost a leader, carried forward once set.
    """

    leader_id: int | None
    is_defeated: bool
    roster_ids: frozenset[int] = frozenset()
    first_fall_month: int | None = None


def _standings(*, savegame: Savegame, before: dict[int, Standing] | None = None) -> dict[int, Standing]:
    before = before or {}
    return {
        faction.id: Standing(
            leader_id=faction.leader_id,
            is_defeated=faction.is_defeated,
            roster_ids=frozenset(Warrior.objects.filter_faction(faction_id=faction.id).values_list("id", flat=True)),
            first_fall_month=before[faction.id].first_fall_month if faction.id in before else None,
        )
        for faction in Faction.objects.for_savegame(savegame_id=savegame.id)
    }


def _count_successions(*, savegame: Savegame, before: dict[int, Standing], report: GameReport) -> dict[int, Standing]:
    """
    Counts the seats that changed hands, the leaders the fyrd raised and the rivals knocked out this month,
    and returns the new standings.
    """
    after = _standings(savegame=savegame, before=before)

    for faction_id, standing in after.items():
        previous = before[faction_id]
        is_player = faction_id == savegame.player_faction_id
        leader_fell = standing.leader_id != previous.leader_id or (standing.is_defeated and not previous.is_defeated)
        if leader_fell and standing.first_fall_month is None:
            after[faction_id] = standing = replace(standing, first_fall_month=report.months_played)

        if standing.leader_id not in (previous.leader_id, None) and not standing.is_defeated:
            raised = standing.leader_id not in previous.roster_ids
            if is_player and raised:
                report.player_leaders_raised += 1
            elif is_player:
                report.player_successions += 1
            elif raised:
                report.rival_leaders_raised += 1
            else:
                report.rival_successions += 1
        if standing.is_defeated and not previous.is_defeated and not is_player:
            report.rival_defeat_months.append(report.months_played)
            report.rival_months_after_first_fall.append(report.months_played - standing.first_fall_month)

    return after


def _record_month(*, savegame: Savegame, month: int) -> MonthRecord:
    return MonthRecord(
        month=month,
        player_men=Warrior.objects.filter_faction(faction_id=savegame.player_faction_id).exclude_dead().count(),
        player_silver=Transaction.objects.current_balance(faction_id=savegame.player_faction_id),
        rival_men=tuple(
            sorted(
                Warrior.objects.filter_faction(faction_id=rival.id).exclude_dead().count()
                for rival in Faction.objects.rivals_in_play(player_faction=savegame.player_faction)
            )
        ),
        rival_silver=tuple(
            sorted(
                Transaction.objects.current_balance(faction_id=rival.id)
                for rival in Faction.objects.rivals_in_play(player_faction=savegame.player_faction)
            )
        ),
    )


def _count_rival_purchases(*, savegame: Savegame) -> int:
    """
    How many items the rivals bought over the whole game, read off their ledgers.

    The ledger is the one record a purchase leaves that loot does not: both end with the item owned,
    and only a purchase is paid for, under the reason "handle_item_bought" writes.
    """
    return Transaction.objects.filter(
        faction__in=Faction.objects.for_savegame(savegame_id=savegame.id).exclude(id=savegame.player_faction_id),
        reason__endswith=" bought",
    ).count()
