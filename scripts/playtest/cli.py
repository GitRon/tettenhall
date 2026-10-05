import argparse
import json
import sys
from collections import Counter
from pathlib import Path

from django.contrib.auth.models import User

from apps.warband.faction.models.culture import Culture
from scripts.playtest.playthrough import play_savegame
from scripts.playtest.policy import POLICIES
from scripts.playtest.report import GameReport

PLAYTEST_USERNAME = "playtest"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m scripts.playtest",
        description="Plays seeded savegames through the real message bus and writes what happened to a JSON file.",
    )
    parser.add_argument("--games", type=int, default=20, help="How many savegames to play (default 20)")
    parser.add_argument("--seed", type=int, default=1, help="Seed of the first game; each next game adds one")
    parser.add_argument("--policy", choices=sorted(POLICIES), default="aggressive", help="When the player marches")
    parser.add_argument("--months", type=int, default=24, help="Month cap per game (default 24)")
    parser.add_argument(
        "--tending", action="store_true", help="The player builds his sanctuary first and tends his wounded"
    )
    parser.add_argument("--output", type=Path, required=True, help="Where the JSON report is written")
    return parser


def summarise(*, report: GameReport) -> str:
    line = (
        f"seed {report.seed}: {report.outcome} after {report.months_played} months, "
        f"fights won {report.fights_won} lost {report.fights_lost}"
    )
    if report.stop_reason is not None:
        line += f", stopped: {report.stop_reason}"
    return line


def main(*, argv: list[str]) -> int:
    arguments = build_parser().parse_args(argv)

    # Without the reference data the new game raises deep inside the generators, so say it up front
    if not Culture.objects.exists():
        sys.stderr.write(
            "No cultures in this database. Run migrate and loaddata first, see docs/patterns/measuring-balance.md\n"
        )
        return 2

    user, _created = User.objects.get_or_create(username=PLAYTEST_USERNAME)
    policy = POLICIES[arguments.policy]
    reports = []

    for seed in range(arguments.seed, arguments.seed + arguments.games):
        report = play_savegame(
            seed=seed, policy=policy, month_cap=arguments.months, user=user, tending=arguments.tending
        )
        reports.append(report.as_dict())
        sys.stdout.write(summarise(report=report) + "\n")
        # After every game, so whatever ran before a crash is kept
        arguments.output.write_text(json.dumps(reports, indent=1), encoding="utf-8")

    outcomes = Counter(report["outcome"] for report in reports)
    sys.stdout.write(", ".join(f"{outcome}: {count}" for outcome, count in sorted(outcomes.items())) + "\n")
    return 0
