import pytest

from apps.skirmish.models.skirmish_warrior_growth import SkirmishWarriorGrowth
from apps.skirmish.tests.factories.skirmish import SkirmishFactory
from apps.skirmish.tests.factories.skirmish_warrior_growth import SkirmishWarriorGrowthFactory
from apps.skirmish.tests.factories.warrior import WarriorFactory


@pytest.mark.django_db
def test_record_growth_creates_the_row_on_the_first_grant():
    skirmish = SkirmishFactory()
    warrior = WarriorFactory(faction=skirmish.attacking_faction)

    growth = SkirmishWarriorGrowth.objects.record_growth(
        skirmish=skirmish, warrior=warrior, faction=warrior.faction, gained_experience=25
    )

    assert growth.gained_experience == 25
    assert SkirmishWarriorGrowth.objects.count() == 1


@pytest.mark.django_db
def test_record_growth_adds_a_second_grant_to_the_first():
    existing = SkirmishWarriorGrowthFactory(gained_experience=25)

    growth = SkirmishWarriorGrowth.objects.record_growth(
        skirmish=existing.skirmish, warrior=existing.warrior, faction=existing.faction, gained_experience=10
    )

    assert growth.gained_experience == 35
    assert SkirmishWarriorGrowth.objects.count() == 1


@pytest.mark.django_db
def test_record_growth_states_the_level_and_the_wage_rather_than_summing_them():
    existing = SkirmishWarriorGrowthFactory(reached_level=2, new_monthly_salary=11)

    growth = SkirmishWarriorGrowth.objects.record_growth(
        skirmish=existing.skirmish,
        warrior=existing.warrior,
        faction=existing.faction,
        reached_level=3,
        new_monthly_salary=12,
    )

    assert growth.reached_level == 3
    assert growth.new_monthly_salary == 12


@pytest.mark.django_db
def test_record_growth_leaves_the_level_and_the_wage_alone_when_no_level_was_reached():
    existing = SkirmishWarriorGrowthFactory(reached_level=2, new_monthly_salary=11)

    growth = SkirmishWarriorGrowth.objects.record_growth(
        skirmish=existing.skirmish, warrior=existing.warrior, faction=existing.faction, gained_experience=10
    )

    assert growth.reached_level == 2
    assert growth.new_monthly_salary == 11


@pytest.mark.django_db
def test_for_skirmish_keeps_another_fights_growth_out():
    growth = SkirmishWarriorGrowthFactory()
    SkirmishWarriorGrowthFactory()

    result = SkirmishWarriorGrowth.objects.for_skirmish(skirmish_id=growth.skirmish_id)

    assert list(result) == [growth]
