from scripts.playtest.report import GameReport, MonthRecord


def test_as_dict_carries_the_timeline():
    report = GameReport(seed=4, policy="even")
    report.timeline.append(MonthRecord(month=1, player_men=5, player_silver=200, rival_men=(3, 4)))

    result = report.as_dict()

    assert result["timeline"] == [{"month": 1, "player_men": 5, "player_silver": 200, "rival_men": (3, 4)}]
