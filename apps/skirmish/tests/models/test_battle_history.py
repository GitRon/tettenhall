from apps.skirmish.tests.factories.battle_history import BattleHistoryFactory


def test_str_returns_the_message():
    battle_history = BattleHistoryFactory.build(message="Round 1 finished.")

    assert str(battle_history) == "Round 1 finished."
