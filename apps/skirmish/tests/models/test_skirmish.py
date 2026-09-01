from apps.skirmish.tests.factories.skirmish import SkirmishFactory


def test_str_returns_the_name():
    skirmish = SkirmishFactory.build(name="Raid on Tettenhall")

    assert str(skirmish) == "Raid on Tettenhall"


def test_rounds_fought_counts_what_is_behind_the_fight():
    skirmish = SkirmishFactory.build(current_round=4)

    assert skirmish.rounds_fought == 3


def test_rounds_fought_is_nothing_before_the_first_blow():
    skirmish = SkirmishFactory.build()

    assert skirmish.rounds_fought == 0
