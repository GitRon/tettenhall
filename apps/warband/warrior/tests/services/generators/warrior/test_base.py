from unittest import mock

import pytest

from apps.warband.faction.models import Culture
from apps.warband.savegame.tests.factories.savegame import SavegameFactory
from apps.warband.skirmish.models.warrior import Warrior
from apps.warband.warrior.services.generators.warrior.fyrd import FyrdWarriorGenerator
from apps.warband.warrior.services.generators.warrior.leader import LeaderWarriorGenerator
from apps.warband.warrior.services.generators.warrior.mercenary import MercenaryWarriorGenerator


@pytest.mark.django_db
def test_process_leaves_a_warrior_whose_experience_is_an_integer():
    """
    Every roll is rounded, so the instance handed back holds the same integer the row does even
    though Django does not re-read after a create. "isqrt" refuses a float, and this is every warrior
    in the pub and every leader on the turn a savegame is created.
    """
    generator = FyrdWarriorGenerator(culture=Culture.objects.first(), faction=None, savegame_id=SavegameFactory().id)

    result = generator.process()

    assert isinstance(result.experience, int)
    assert result.level == Warrior.objects.get(pk=result.pk).level


@pytest.mark.django_db
def test_process_rounds_a_sub_one_health_roll_up_to_a_point():
    """
    The band between zero and one is the one a truncating column turns into a warrior with no health
    at all, so it is patched rather than waited for.
    """
    generator = FyrdWarriorGenerator(culture=Culture.objects.first(), faction=None, savegame_id=SavegameFactory().id)

    with mock.patch("apps.warband.warrior.services.generators.warrior.base.random.gauss", return_value=0.6):
        result = generator.process()

    assert result.max_health == 1
    assert Warrior.objects.get(pk=result.pk).max_health == 1


@pytest.mark.django_db
def test_process_rounds_a_sub_one_morale_roll_up_to_a_point():
    generator = FyrdWarriorGenerator(culture=Culture.objects.first(), faction=None, savegame_id=SavegameFactory().id)

    with mock.patch("apps.warband.warrior.services.generators.warrior.base.random.gauss", return_value=0.6):
        result = generator.process()

    assert result.max_morale == 1
    assert Warrior.objects.get(pk=result.pk).max_morale == 1


@pytest.mark.django_db
def test_process_rerolls_a_roll_that_rounds_to_zero():
    """
    Every roll comes up at minus five first, which the floor and the rounding turn into the zero the
    guards refuse, and then at twelve. A "return_value" the guards reject would spin for ever, so the
    second value is what proves the retry fires and the loops terminate.
    """
    generator = FyrdWarriorGenerator(culture=Culture.objects.first(), faction=None, savegame_id=SavegameFactory().id)

    with mock.patch("apps.warband.warrior.services.generators.warrior.base.random.gauss", side_effect=[-5, 12] * 10):
        result = generator.process()

    assert result.max_health == 12
    assert result.max_morale == 12


@pytest.mark.django_db
def test_process_keeps_a_progress_roll_at_its_ceiling():
    """
    A roll just above a hundred rounds down onto the ceiling rather than over it, so the guard takes
    it instead of asking for another one.
    """
    generator = FyrdWarriorGenerator(culture=Culture.objects.first(), faction=None, savegame_id=SavegameFactory().id)

    with mock.patch("apps.warband.warrior.services.generators.warrior.base.random.gauss", return_value=100.4):
        result = generator.process()

    assert result.health_progress == 100
    assert result.morale_progress == 100


@pytest.mark.django_db
def test_process_floors_the_stats_at_the_generator_minimum():
    """
    A leader sits at STATS_MIN = 4, so a roll that rounds to one is lifted to the minimum instead of
    being re-rolled - which is why the two stats need no guard.
    """
    generator = LeaderWarriorGenerator(culture=Culture.objects.first(), faction=None, savegame_id=SavegameFactory().id)

    with mock.patch("apps.warband.warrior.services.generators.warrior.base.random.gauss", return_value=0.6):
        result = generator.process()

    assert result.strength == 4
    assert result.dexterity == 4


@pytest.mark.django_db
def test_process_prices_an_average_levy_against_the_shared_yardstick():
    """
    Every roll comes out at its own mean, so this is the average man of his kind and the price is the
    archetype's alone rather than a draw. A levy lands at half a mercenary's wage, and this is the
    test that says so: priced against each archetype's own mean instead, every archetype comes out at
    150 and nothing notices.
    """
    generator = FyrdWarriorGenerator(culture=Culture.objects.first(), faction=None, savegame_id=SavegameFactory().id)

    with mock.patch(
        "apps.warband.warrior.services.generators.warrior.base.random.gauss", side_effect=lambda mu, sigma: mu
    ):
        result = generator.process()

    assert result.recruitment_price == 150
    assert result.monthly_salary == 75


@pytest.mark.django_db
def test_process_prices_an_average_mercenary_against_the_shared_yardstick():
    """
    The yardstick is this man's own means, so he is the one archetype whose price would be the same
    either way and this is not the test that would catch the normalisation coming back - the two
    either side of it are. What it pins is the scale itself: a professional fighting man at 150 a
    month is what the hall's revenue and "RivalIncome" are read against, so moving the yardstick has
    to fail something and this is the something.
    """
    generator = MercenaryWarriorGenerator(
        culture=Culture.objects.first(), faction=None, savegame_id=SavegameFactory().id
    )

    with mock.patch(
        "apps.warband.warrior.services.generators.warrior.base.random.gauss", side_effect=lambda mu, sigma: mu
    ):
        result = generator.process()

    assert result.recruitment_price == 300
    assert result.monthly_salary == 150


@pytest.mark.django_db
def test_process_prices_an_average_leader_against_the_shared_yardstick():
    generator = LeaderWarriorGenerator(culture=Culture.objects.first(), faction=None, savegame_id=SavegameFactory().id)

    with mock.patch(
        "apps.warband.warrior.services.generators.warrior.base.random.gauss", side_effect=lambda mu, sigma: mu
    ):
        result = generator.process()

    assert result.recruitment_price == 260
    assert result.monthly_salary == 130


@pytest.mark.django_db
def test_process_equips_the_warrior_when_both_rolls_come_up():
    """
    Whether a warrior gets a weapon and an armour is a dice roll, so the roll is patched at the
    boundary instead of leaving these two branches to chance.
    """
    generator = FyrdWarriorGenerator(culture=Culture.objects.first(), faction=None, savegame_id=SavegameFactory().id)

    # Below both chances, so both items are generated
    with mock.patch("apps.warband.warrior.services.generators.warrior.base.random.uniform", return_value=0):
        result = generator.process()

    assert result.weapon is not None
    assert result.armor is not None


@pytest.mark.django_db
def test_process_leaves_the_warrior_bare_when_both_rolls_fail():
    generator = FyrdWarriorGenerator(culture=Culture.objects.first(), faction=None, savegame_id=SavegameFactory().id)

    # Above both chances, so neither item is generated
    with mock.patch("apps.warband.warrior.services.generators.warrior.base.random.uniform", return_value=1):
        result = generator.process()

    assert result.weapon is None
    assert result.armor is None


@pytest.mark.django_db
def test_process_stamps_the_levy_baseline_on_the_warrior():
    """
    The baseline travels with the warrior because the archetypes do not share one, and a levy carrying
    a mercenary's mean would swing at half strength for the whole savegame.
    """
    generator = FyrdWarriorGenerator(culture=Culture.objects.first(), faction=None, savegame_id=SavegameFactory().id)

    result = generator.process()

    assert result.strength_baseline == FyrdWarriorGenerator.STATS_MU
    assert Warrior.objects.get(pk=result.pk).strength_baseline == FyrdWarriorGenerator.STATS_MU


@pytest.mark.django_db
def test_process_stamps_the_leader_baseline_on_the_warrior():
    generator = LeaderWarriorGenerator(culture=Culture.objects.first(), faction=None, savegame_id=SavegameFactory().id)

    result = generator.process()

    assert result.strength_baseline == LeaderWarriorGenerator.STATS_MU


@pytest.mark.django_db
def test_process_stamps_the_levy_spread_on_the_warrior():
    """
    The spread travels for the same reason the baseline does: it is what an exceptional roll is
    recognised by, and the archetypes differ in it by nearly a factor of three.
    """
    generator = FyrdWarriorGenerator(culture=Culture.objects.first(), faction=None, savegame_id=SavegameFactory().id)

    result = generator.process()

    assert result.stats_spread == FyrdWarriorGenerator.STATS_SIGMA
    assert Warrior.objects.get(pk=result.pk).stats_spread == FyrdWarriorGenerator.STATS_SIGMA


@pytest.mark.django_db
def test_process_stamps_the_levy_floor_on_the_warrior():
    """
    The floor travels too, because it is the whole of the downward end: the roll is clamped to it, so
    that is where a quarter of every levy lands and the only position a feeble man can be in.
    """
    generator = FyrdWarriorGenerator(culture=Culture.objects.first(), faction=None, savegame_id=SavegameFactory().id)

    result = generator.process()

    assert result.stats_minimum == FyrdWarriorGenerator.STATS_MIN
    assert Warrior.objects.get(pk=result.pk).stats_minimum == FyrdWarriorGenerator.STATS_MIN


@pytest.mark.django_db
def test_process_stamps_the_levy_health_draw_on_the_warrior():
    """
    Health carries its own mean and spread rather than borrowing the stats ones: a fyrd man is rolled
    for ten health against a spread of ten and for five strength against a spread of five, and the
    two pairs stand in no fixed ratio across the archetypes.
    """
    generator = FyrdWarriorGenerator(culture=Culture.objects.first(), faction=None, savegame_id=SavegameFactory().id)

    result = generator.process()

    assert result.health_baseline == FyrdWarriorGenerator.HEALTH_MU
    assert result.health_spread == FyrdWarriorGenerator.HEALTH_SIGMA


@pytest.mark.django_db
def test_process_stamps_the_levy_morale_draw_on_the_warrior():
    generator = FyrdWarriorGenerator(culture=Culture.objects.first(), faction=None, savegame_id=SavegameFactory().id)

    result = generator.process()

    assert result.morale_baseline == FyrdWarriorGenerator.MORALE_MU
    assert result.morale_spread == FyrdWarriorGenerator.MORALE_SIGMA


@pytest.mark.django_db
def test_process_draws_the_warriors_nickname_variant_once():
    """
    Which wording his epithet takes is settled when he is generated and then held, so he reads the
    same on every page for the rest of the savegame.
    """
    generator = FyrdWarriorGenerator(culture=Culture.objects.first(), faction=None, savegame_id=SavegameFactory().id)

    with mock.patch("apps.warband.warrior.services.generators.warrior.base.random.randrange", return_value=2):
        result = generator.process()

    assert result.nickname_variant == 2
    assert Warrior.objects.get(pk=result.pk).nickname_variant == 2
