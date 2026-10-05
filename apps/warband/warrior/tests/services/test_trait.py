from unittest import mock

import pytest

from apps.warband.skirmish.choices.blow_outcome import BlowOutcomeChoices
from apps.warband.skirmish.tests.factories.skirmish import SkirmishFactory
from apps.warband.skirmish.tests.factories.skirmish_blow import SkirmishBlowFactory
from apps.warband.skirmish.tests.factories.warrior import WarriorFactory
from apps.warband.warrior.models.trait_type import TraitType
from apps.warband.warrior.services.trait import InnateTraitDrawService, TraitEarningService
from apps.warband.warrior.tests.factories.trait import TraitFactory
from apps.warband.warrior.tests.factories.trait_type import TraitTypeFactory

SHAKEN_HITS = TraitEarningService.SHAKEN_HITS_TAKEN
CHARMED_SWINGS = TraitEarningService.CHARMED_SWINGS_SURVIVED
HEADTAKER_ROLLS = TraitEarningService.HEADTAKER_CEILING_ROLLS
SHIELD_WALL_BLOWS = TraitEarningService.SHIELD_WALL_BLOWS_ABSORBED


def _shipped(hook: str) -> TraitType:
    return TraitType.objects.get(hook=hook)


def _blows_taken(*, warrior, skirmish, count: int, outcome: int) -> None:
    SkirmishBlowFactory.create_batch(count, skirmish=skirmish, defender=warrior, outcome=outcome)


# InnateTraitDrawService


@pytest.mark.django_db
def test_draw_gives_most_men_nothing():
    with mock.patch("apps.warband.warrior.services.trait.random.uniform", return_value=0.5):
        result = InnateTraitDrawService().process()

    assert result == []


@pytest.mark.django_db
def test_draw_gives_one_innate_trait_below_the_first_chance():
    with mock.patch("apps.warband.warrior.services.trait.random.uniform", return_value=0.3):
        result = InnateTraitDrawService().process()

    assert [trait_type.source for trait_type in result] == [TraitType.SourceChoices.SOURCE_INNATE]


@pytest.mark.django_db
def test_draw_gives_two_traits_of_different_groups_below_the_second_chance():
    # The shuffle is patched to leave the catalogue in order, which puts the two "build" traits first:
    # the second of them has to be skipped for one of another group
    with (
        mock.patch("apps.warband.warrior.services.trait.random.uniform", return_value=0.05),
        mock.patch("apps.warband.warrior.services.trait.random.shuffle"),
    ):
        result = InnateTraitDrawService().process()

    assert [trait_type.hook for trait_type in result] == ["bull-necked", "nimble"]


# TraitEarningService


@pytest.mark.django_db
def test_earning_grants_shaken_for_enough_hits_in_one_fight():
    skirmish = SkirmishFactory()
    warrior = WarriorFactory(faction=skirmish.defending_faction)
    _blows_taken(warrior=warrior, skirmish=skirmish, count=SHAKEN_HITS, outcome=BlowOutcomeChoices.OUTCOME_HIT)

    result = TraitEarningService(warrior=warrior, skirmish=skirmish).process()

    assert result == _shipped("shaken")


@pytest.mark.django_db
def test_earning_counts_only_this_fights_hits_for_shaken():
    skirmish = SkirmishFactory()
    warrior = WarriorFactory(faction=skirmish.defending_faction)
    _blows_taken(warrior=warrior, skirmish=skirmish, count=SHAKEN_HITS - 1, outcome=BlowOutcomeChoices.OUTCOME_HIT)
    _blows_taken(
        warrior=warrior, skirmish=SkirmishFactory(), count=SHAKEN_HITS - 1, outcome=BlowOutcomeChoices.OUTCOME_HIT
    )

    result = TraitEarningService(warrior=warrior, skirmish=skirmish).process()

    assert result is None


@pytest.mark.django_db
def test_earning_grants_charmed_for_a_fight_of_swings_that_never_landed():
    skirmish = SkirmishFactory()
    warrior = WarriorFactory(faction=skirmish.defending_faction)
    _blows_taken(
        warrior=warrior, skirmish=skirmish, count=CHARMED_SWINGS - 1, outcome=BlowOutcomeChoices.OUTCOME_MISSED
    )
    _blows_taken(warrior=warrior, skirmish=skirmish, count=1, outcome=BlowOutcomeChoices.OUTCOME_ABSORBED)

    result = TraitEarningService(warrior=warrior, skirmish=skirmish).process()

    assert result == _shipped("charmed")


@pytest.mark.django_db
def test_earning_does_not_count_a_blow_never_thrown_as_a_swing_survived():
    skirmish = SkirmishFactory()
    warrior = WarriorFactory(faction=skirmish.defending_faction)
    _blows_taken(
        warrior=warrior, skirmish=skirmish, count=CHARMED_SWINGS - 1, outcome=BlowOutcomeChoices.OUTCOME_MISSED
    )
    _blows_taken(warrior=warrior, skirmish=skirmish, count=1, outcome=BlowOutcomeChoices.OUTCOME_NOT_THROWN)

    result = TraitEarningService(warrior=warrior, skirmish=skirmish).process()

    assert result is None


@pytest.mark.django_db
def test_earning_withholds_charmed_from_a_man_who_was_hit_once():
    skirmish = SkirmishFactory()
    warrior = WarriorFactory(faction=skirmish.defending_faction)
    _blows_taken(warrior=warrior, skirmish=skirmish, count=CHARMED_SWINGS, outcome=BlowOutcomeChoices.OUTCOME_MISSED)
    _blows_taken(warrior=warrior, skirmish=skirmish, count=1, outcome=BlowOutcomeChoices.OUTCOME_HIT)

    result = TraitEarningService(warrior=warrior, skirmish=skirmish).process()

    assert result is None


@pytest.mark.django_db
def test_earning_grants_headtaker_for_enough_ceiling_rolls_over_a_career():
    skirmish = SkirmishFactory()
    warrior = WarriorFactory(faction=skirmish.attacking_faction)
    # "2d6" with a modifier of one tops out at 13, spread over two fights to show the count is a career's
    SkirmishBlowFactory.create_batch(HEADTAKER_ROLLS - 1, skirmish=skirmish, attacker=warrior, attack_roll=13)
    SkirmishBlowFactory(attacker=warrior, attack_roll=13)
    SkirmishBlowFactory(skirmish=skirmish, attacker=warrior, attack_roll=12)

    result = TraitEarningService(warrior=warrior, skirmish=skirmish).process()

    assert result == _shipped("headtaker")


@pytest.mark.django_db
def test_earning_skips_blows_with_no_die_thrown_for_headtaker():
    skirmish = SkirmishFactory()
    warrior = WarriorFactory(faction=skirmish.attacking_faction)
    SkirmishBlowFactory.create_batch(HEADTAKER_ROLLS - 1, skirmish=skirmish, attacker=warrior, attack_roll=13)
    SkirmishBlowFactory(
        skirmish=skirmish,
        attacker=warrior,
        attack_dice="",
        attack_modifier=None,
        attack_roll=None,
        outcome=BlowOutcomeChoices.OUTCOME_NOT_THROWN,
    )

    result = TraitEarningService(warrior=warrior, skirmish=skirmish).process()

    assert result is None


@pytest.mark.django_db
def test_earning_grants_shield_wall_man_for_enough_blows_absorbed_over_a_career():
    skirmish = SkirmishFactory()
    warrior = WarriorFactory(faction=skirmish.defending_faction)
    # Split so that neither fight alone reaches the threshold, and so that this one also keeps him from
    # being charmed: a hit lands in it
    _blows_taken(
        warrior=warrior, skirmish=skirmish, count=SHIELD_WALL_BLOWS - 1, outcome=BlowOutcomeChoices.OUTCOME_ABSORBED
    )
    _blows_taken(warrior=warrior, skirmish=skirmish, count=1, outcome=BlowOutcomeChoices.OUTCOME_HIT)
    _blows_taken(warrior=warrior, skirmish=SkirmishFactory(), count=1, outcome=BlowOutcomeChoices.OUTCOME_ABSORBED)

    result = TraitEarningService(warrior=warrior, skirmish=skirmish).process()

    assert result == _shipped("shield-wall-man")


@pytest.mark.django_db
def test_earning_skips_a_trait_whose_group_the_man_already_has():
    skirmish = SkirmishFactory()
    warrior = WarriorFactory(faction=skirmish.defending_faction)
    TraitFactory(warrior=warrior, type=_shipped("steady"))
    _blows_taken(warrior=warrior, skirmish=skirmish, count=SHAKEN_HITS, outcome=BlowOutcomeChoices.OUTCOME_HIT)

    result = TraitEarningService(warrior=warrior, skirmish=skirmish).process()

    assert result is None


@pytest.mark.django_db
def test_earning_grants_nothing_past_the_cap():
    skirmish = SkirmishFactory()
    warrior = WarriorFactory(faction=skirmish.defending_faction)
    for hook in ("bull-necked", "nimble", "drunkard"):
        TraitFactory(warrior=warrior, type=_shipped(hook))
    _blows_taken(warrior=warrior, skirmish=skirmish, count=SHAKEN_HITS, outcome=BlowOutcomeChoices.OUTCOME_HIT)

    result = TraitEarningService(warrior=warrior, skirmish=skirmish).process()

    assert result is None


@pytest.mark.django_db
def test_earning_raises_for_an_earned_trait_nobody_wrote_a_rule_for():
    skirmish = SkirmishFactory()
    warrior = WarriorFactory(faction=skirmish.defending_faction)
    TraitTypeFactory(hook="pious", source=TraitType.SourceChoices.SOURCE_EARNED)

    with pytest.raises(KeyError):
        TraitEarningService(warrior=warrior, skirmish=skirmish).process()
