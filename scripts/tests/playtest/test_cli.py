import json

import pytest

from apps.warband.faction.models.culture import Culture
from scripts.playtest.cli import build_parser, main, summarise
from scripts.playtest.report import GameReport


def test_build_parser_refuses_an_unknown_policy():
    with pytest.raises(SystemExit, match=r"^2$"):
        build_parser().parse_args(["--policy", "cautious", "--output", "report.json"])


def test_summarise_a_game_that_ran():
    report = GameReport(seed=3, policy="even", outcome="Won", months_played=7, fights_won=4, fights_lost=1)

    assert summarise(report=report) == "seed 3: Won after 7 months, fights won 4 lost 1"


def test_summarise_names_why_a_game_was_stopped():
    report = GameReport(seed=3, policy="even", outcome="Running", months_played=2, stop_reason="stuck")

    assert summarise(report=report) == "seed 3: Running after 2 months, fights won 0 lost 0, stopped: stuck"


@pytest.mark.django_db
def test_main_writes_every_game_to_the_report(tmp_path, queuebie_registry):
    output = tmp_path / "report.json"

    result = main(argv=["--games", "2", "--months", "1", "--policy", "prudent", "--output", str(output)])

    assert result == 0
    assert [game["seed"] for game in json.loads(output.read_text(encoding="utf-8"))] == [1, 2]


@pytest.mark.django_db
def test_main_plays_a_tending_player_when_asked(tmp_path, queuebie_registry):
    output = tmp_path / "report.json"

    main(argv=["--games", "1", "--months", "1", "--tending", "--output", str(output)])

    assert [game["tending"] for game in json.loads(output.read_text(encoding="utf-8"))] == [True]


@pytest.mark.django_db
def test_main_plays_a_geld_player_when_asked(tmp_path, queuebie_registry):
    output = tmp_path / "report.json"

    main(argv=["--games", "1", "--months", "1", "--geld", "--output", str(output)])

    assert [game["geld"] for game in json.loads(output.read_text(encoding="utf-8"))] == [True]


@pytest.mark.django_db
def test_main_refuses_a_database_without_reference_data(tmp_path):
    Culture.objects.all().delete()

    result = main(argv=["--output", str(tmp_path / "report.json")])

    assert result == 2
