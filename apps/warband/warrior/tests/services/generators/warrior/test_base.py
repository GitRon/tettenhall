from statistics import NormalDist
from unittest import mock

import pytest

from apps.warband.faction.models import Culture
from apps.warband.savegame.tests.factories.savegame import SavegameFactory
from apps.warband.skirmish.models.warrior import Warrior
from apps.warband.warrior.choices.nickname import NicknameStateChoices
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


def test_roll_stat_rerolls_a_roll_below_the_generator_minimum():
    """
    A leader sits at STATS_MIN = 4, so a roll that rounds to one is thrown away rather than lifted onto
    the minimum, which would pile the whole left tail onto the floor.
    """
    generator = LeaderWarriorGenerator(culture=None, faction=None, savegame_id=0)

    with mock.patch("apps.warband.warrior.services.generators.warrior.base.random.gauss", side_effect=[0.6, 5]):
        result = generator.roll_stat()

    assert result == 5


def test_roll_stat_keeps_a_roll_on_the_generator_minimum():
    generator = LeaderWarriorGenerator(culture=None, faction=None, savegame_id=0)

    with mock.patch("apps.warband.warrior.services.generators.warrior.base.random.gauss", return_value=4.4):
        result = generator.roll_stat()

    assert result == 4


# Every guarded draw a generator makes, as (mean, spread, lowest value kept)
GUARDED_DRAWS = [
    pytest.param(generator.STATS_MU, generator.STATS_SIGMA, generator.STATS_MIN, id=f"{generator.__name__}-stats")
    for generator in (FyrdWarriorGenerator, MercenaryWarriorGenerator, LeaderWarriorGenerator)
] + [
    pytest.param(mu, sigma, 1, id=f"{generator.__name__}-{attribute}")
    for generator in (FyrdWarriorGenerator, MercenaryWarriorGenerator, LeaderWarriorGenerator)
    for attribute, mu, sigma in (
        ("health", generator.HEALTH_MU, generator.HEALTH_SIGMA),
        ("morale", generator.MORALE_MU, generator.MORALE_SIGMA),
    )
]


@pytest.mark.parametrize(("mu", "sigma", "minimum"), GUARDED_DRAWS)
def test_generator_keeps_its_average_man_on_its_own_mean(mu, sigma, minimum):
    """
    Throwing the rolls below the minimum away raises the mean of the ones kept, by the mean of a
    normal distribution cut off at that point. The baselines stamped on a warrior are the generator's
    means, and a fight scales a blow by strength against its baseline, so a mean that drifted off it
    would be a standing bonus to every man of the archetype. A spread of five on a levy's strength
    would put his average man two points above the baseline he swings against.
    """
    cut = (minimum - 0.5 - mu) / sigma

    drift = sigma * NormalDist().pdf(cut) / (1 - NormalDist().cdf(cut))

    assert drift < 0.5


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
    """
    His price is still the yardstick's answer even though no wage comes out of it: what a leader is
    worth is what a captor gets for him, and "slavery_selling_price" reads this column.
    """
    generator = LeaderWarriorGenerator(culture=Culture.objects.first(), faction=None, savegame_id=SavegameFactory().id)

    with mock.patch(
        "apps.warband.warrior.services.generators.warrior.base.random.gauss", side_effect=lambda mu, sigma: mu
    ):
        result = generator.process()

    assert result.recruitment_price == 260
    assert result.monthly_salary == 0


@pytest.mark.django_db
def test_process_leaves_the_leader_off_the_wage_bill():
    """
    The one archetype that draws nothing, on an unpatched draw so it holds for every leader rather
    than for the average one. The price beside it is what says only the wage was zeroed: a leader who
    came out at zero on both would have no value to a captor either, and the two other archetype
    price tests are what stop a wage of zero spreading to them.
    """
    generator = LeaderWarriorGenerator(culture=Culture.objects.first(), faction=None, savegame_id=SavegameFactory().id)

    result = generator.process()

    assert result.monthly_salary == 0
    assert result.recruitment_price > 0


@pytest.mark.django_db
def test_process_puts_a_levy_on_the_wage_bill():
    """
    The other side of "draws_a_wage", so the flag cannot be flipped on the base class and take every
    archetype off the payroll with it.
    """
    generator = FyrdWarriorGenerator(culture=Culture.objects.first(), faction=None, savegame_id=SavegameFactory().id)

    result = generator.process()

    assert result.monthly_salary > 0
    assert Warrior.objects.get(pk=result.pk).monthly_salary == result.monthly_salary


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
    recognised by, and the archetypes differ in it by a factor of two.
    """
    generator = FyrdWarriorGenerator(culture=Culture.objects.first(), faction=None, savegame_id=SavegameFactory().id)

    result = generator.process()

    assert result.stats_spread == FyrdWarriorGenerator.STATS_SIGMA
    assert Warrior.objects.get(pk=result.pk).stats_spread == FyrdWarriorGenerator.STATS_SIGMA


@pytest.mark.django_db
def test_process_stamps_the_levy_floor_on_the_warrior():
    """
    The floor travels too, because it is the downward end of the draw and the clamp on the cut a
    feeble man's epithet is measured against.
    """
    generator = FyrdWarriorGenerator(culture=Culture.objects.first(), faction=None, savegame_id=SavegameFactory().id)

    result = generator.process()

    assert result.stats_minimum == FyrdWarriorGenerator.STATS_MIN
    assert Warrior.objects.get(pk=result.pk).stats_minimum == FyrdWarriorGenerator.STATS_MIN


@pytest.mark.django_db
def test_process_stamps_the_levy_health_draw_on_the_warrior():
    """
    Health carries its own mean and spread rather than borrowing the stats ones: a fyrd man is rolled
    for ten health against a spread of four and for five strength against a spread of two, and the
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


@pytest.mark.django_db
def test_process_stamps_the_warriors_nickname_state_against_his_own_archetype():
    """
    A fyrd man's nerve is drawn at a mean of five against a spread of three, so thirteen is two and
    two thirds spreads out and a wonder among his own kind. Only the nerve roll is handed thirteen:
    strength shares his mean of five against a spread of two, so thirteen there would be four spreads
    out and would outrank it.
    """
    generator = FyrdWarriorGenerator(culture=Culture.objects.first(), faction=None, savegame_id=SavegameFactory().id)

    with mock.patch(
        "apps.warband.warrior.services.generators.warrior.base.random.gauss",
        side_effect=lambda mu, sigma: 13 if sigma == FyrdWarriorGenerator.MORALE_SIGMA else mu,
    ):
        result = generator.process()

    assert result.nickname_state == NicknameStateChoices.MORALE_FAR
    assert Warrior.objects.get(pk=result.pk).nickname_state == NicknameStateChoices.MORALE_FAR


@pytest.mark.django_db
def test_process_leaves_an_ordinary_man_unnamed():
    """
    Every attribute landing exactly on its own mean is nobody worth a name, and null is what the
    ratchet later looks for - a man stamped with something here could never earn one.
    """
    generator = FyrdWarriorGenerator(culture=Culture.objects.first(), faction=None, savegame_id=SavegameFactory().id)

    with mock.patch(
        "apps.warband.warrior.services.generators.warrior.base.random.gauss",
        side_effect=lambda mu, sigma: mu,
    ):
        result = generator.process()

    assert result.nickname_state is None
    assert Warrior.objects.get(pk=result.pk).nickname_state is None


@pytest.mark.django_db
def test_process_writes_the_innate_traits_he_is_born_with():
    generator = MercenaryWarriorGenerator(
        culture=Culture.objects.first(), faction=None, savegame_id=SavegameFactory().id
    )

    # The one module-wide "random" is patched here, so the gear rolls see the same 0.3 and he is armed
    with mock.patch("apps.warband.warrior.services.trait.random.uniform", return_value=0.3):
        result = generator.process()

    assert result.traits.count() == 1


@pytest.mark.django_db
def test_process_keeps_a_levy_rolled_at_every_floor_on_the_wage_bill():
    """
    Every attribute at its floor and a base price of one truncate to a price of nothing, and half of
    nothing is a wage of nothing - a levy off the payroll and free to hire. Patched rather than
    waited for, because it is the thin end of three draws at once.
    """
    generator = FyrdWarriorGenerator(culture=Culture.objects.first(), faction=None, savegame_id=SavegameFactory().id)

    with mock.patch("apps.warband.warrior.services.generators.warrior.base.random.gauss", return_value=0.6):
        result = generator.process()

    assert result.recruitment_price == 1
    assert result.monthly_salary == 1


@pytest.mark.django_db
def test_process_gives_the_warrior_a_face_of_his_own():
    """Drawn once and stored, so the row carries it rather than anything deriving it at render time."""
    generator = FyrdWarriorGenerator(culture=Culture.objects.first(), faction=None, savegame_id=SavegameFactory().id)

    result = generator.process()

    assert result.portrait_face is not None
    assert Warrior.objects.get(pk=result.pk).portrait_face == result.portrait_face
