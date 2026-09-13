from apps.warband.skirmish.models.warrior import Warrior
from apps.warband.templatetags.muster import still_up


def test_still_up_counts_only_the_men_on_their_feet():
    band = [
        Warrior(condition=Warrior.ConditionChoices.CONDITION_HEALTHY),
        Warrior(condition=Warrior.ConditionChoices.CONDITION_UNCONSCIOUS),
        Warrior(condition=Warrior.ConditionChoices.CONDITION_FLEEING),
        Warrior(condition=Warrior.ConditionChoices.CONDITION_DEAD),
        Warrior(condition=Warrior.ConditionChoices.CONDITION_HEALTHY),
    ]

    result = still_up(band)

    assert result == 2


def test_still_up_of_a_band_with_nobody_left():
    result = still_up([Warrior(condition=Warrior.ConditionChoices.CONDITION_DEAD)])

    assert result == 0
