import pytest

from apps.item.models.item_type import ItemType
from apps.item.tests.factories.item import ItemFactory
from apps.item.tests.factories.item_type import ItemTypeFactory
from apps.skirmish.models.skirmish_spoil import SkirmishSpoil
from apps.skirmish.projections.skirmish_report import SkirmishReport
from apps.skirmish.tests.factories.skirmish import SkirmishFactory
from apps.skirmish.tests.factories.skirmish_spoil import SkirmishSpoilFactory
from apps.skirmish.tests.factories.skirmish_warrior_growth import SkirmishWarriorGrowthFactory
from apps.skirmish.tests.factories.warrior import WarriorFactory


@pytest.mark.django_db
def test_for_skirmish_takes_the_roster_of_the_side_that_marched():
    skirmish = SkirmishFactory()
    own_warrior = WarriorFactory(faction=skirmish.attacking_faction)
    skirmish.attacking_warriors.add(own_warrior)
    skirmish.defending_warriors.add(WarriorFactory(faction=skirmish.defending_faction))

    report = SkirmishReport.for_skirmish(skirmish=skirmish, faction=skirmish.attacking_faction)

    assert report.own_warrior_ids == {own_warrior.id}


@pytest.mark.django_db
def test_for_skirmish_takes_the_roster_of_the_side_that_was_attacked():
    skirmish = SkirmishFactory()
    own_warrior = WarriorFactory(faction=skirmish.defending_faction)
    skirmish.defending_warriors.add(own_warrior)
    skirmish.attacking_warriors.add(WarriorFactory(faction=skirmish.attacking_faction))

    report = SkirmishReport.for_skirmish(skirmish=skirmish, faction=skirmish.defending_faction)

    assert report.own_warrior_ids == {own_warrior.id}


@pytest.mark.django_db
def test_for_skirmish_measures_against_the_gear_the_faction_is_wearing():
    skirmish = SkirmishFactory()
    weapon = ItemFactory(
        savegame=skirmish.attacking_faction.savegame,
        owner=skirmish.attacking_faction,
        type=ItemTypeFactory(base_value="1d6", function=ItemType.FunctionChoices.FUNCTION_WEAPON),
        modifier=2,
    )
    WarriorFactory(faction=skirmish.attacking_faction, weapon=weapon)

    report = SkirmishReport.for_skirmish(skirmish=skirmish, faction=skirmish.attacking_faction)

    assert report.best_worn_weapon_value == weapon.expectancy_value
    assert report.best_worn_armor_value == 0.0


@pytest.mark.django_db
def test_for_skirmish_reads_only_the_faction_s_own_growth():
    skirmish = SkirmishFactory()
    own_growth = SkirmishWarriorGrowthFactory(skirmish=skirmish, faction=skirmish.attacking_faction)
    SkirmishWarriorGrowthFactory(skirmish=skirmish, faction=skirmish.defending_faction)

    report = SkirmishReport.for_skirmish(skirmish=skirmish, faction=skirmish.attacking_faction)

    assert report.growth_list == [own_growth]


@pytest.mark.django_db
def test_is_victory_is_true_for_the_side_that_won():
    skirmish = SkirmishFactory()
    skirmish.victorious_faction = skirmish.attacking_faction
    skirmish.save()

    report = SkirmishReport.for_skirmish(skirmish=skirmish, faction=skirmish.attacking_faction)

    assert report.is_victory is True


@pytest.mark.django_db
def test_is_victory_is_false_for_the_side_that_lost():
    skirmish = SkirmishFactory()
    skirmish.victorious_faction = skirmish.attacking_faction
    skirmish.save()

    report = SkirmishReport.for_skirmish(skirmish=skirmish, faction=skirmish.defending_faction)

    assert report.is_victory is False


@pytest.mark.django_db
def test_items_won_flags_a_weapon_nobody_in_the_warband_can_match():
    skirmish = SkirmishFactory()
    loser = WarriorFactory(faction=skirmish.defending_faction)
    item = ItemFactory(
        savegame=skirmish.attacking_faction.savegame,
        type=ItemTypeFactory(base_value="4d4", function=ItemType.FunctionChoices.FUNCTION_WEAPON),
        modifier=5,
    )
    SkirmishSpoilFactory(
        skirmish=skirmish,
        faction=skirmish.attacking_faction,
        kind=SkirmishSpoil.KindChoices.KIND_ITEM_TAKEN,
        item=item,
        warrior=loser,
    )

    report = SkirmishReport.for_skirmish(skirmish=skirmish, faction=skirmish.attacking_faction)

    assert report.items_won[0].is_upgrade is True
    assert report.items_won[0].taken_from == loser


@pytest.mark.django_db
def test_items_won_leaves_armor_unflagged_when_the_warband_wears_better():
    skirmish = SkirmishFactory()
    armor_type = ItemTypeFactory(base_value="1d4", function=ItemType.FunctionChoices.FUNCTION_ARMOR)
    worn_armor = ItemFactory(
        savegame=skirmish.attacking_faction.savegame,
        owner=skirmish.attacking_faction,
        type=armor_type,
        modifier=9,
    )
    WarriorFactory(faction=skirmish.attacking_faction, armor=worn_armor)
    SkirmishSpoilFactory(
        skirmish=skirmish,
        faction=skirmish.attacking_faction,
        kind=SkirmishSpoil.KindChoices.KIND_ITEM_TAKEN,
        item=ItemFactory(savegame=skirmish.attacking_faction.savegame, type=armor_type, modifier=0),
    )

    report = SkirmishReport.for_skirmish(skirmish=skirmish, faction=skirmish.attacking_faction)

    assert report.items_won[0].is_upgrade is False


@pytest.mark.django_db
def test_items_lost_names_only_the_gear_taken_off_the_faction_s_own_men():
    skirmish = SkirmishFactory()
    own_warrior = WarriorFactory(faction=skirmish.attacking_faction)
    skirmish.attacking_warriors.add(own_warrior)
    stripped = SkirmishSpoilFactory(
        skirmish=skirmish,
        faction=skirmish.defending_faction,
        kind=SkirmishSpoil.KindChoices.KIND_ITEM_TAKEN,
        item=ItemFactory(savegame=skirmish.attacking_faction.savegame),
        warrior=own_warrior,
    )
    # The winner's own dead are stripped too, and that is not a loss of the attacker's
    SkirmishSpoilFactory(
        skirmish=skirmish,
        faction=skirmish.defending_faction,
        kind=SkirmishSpoil.KindChoices.KIND_ITEM_TAKEN,
        item=ItemFactory(savegame=skirmish.attacking_faction.savegame),
        warrior=WarriorFactory(faction=skirmish.defending_faction),
    )

    report = SkirmishReport.for_skirmish(skirmish=skirmish, faction=skirmish.attacking_faction)

    assert report.items_lost == [stripped]


@pytest.mark.django_db
def test_the_purse_and_the_contract_are_counted_apart_and_summed():
    skirmish = SkirmishFactory()
    SkirmishSpoilFactory(
        skirmish=skirmish,
        faction=skirmish.attacking_faction,
        kind=SkirmishSpoil.KindChoices.KIND_SILVER_LOOTED,
        amount=12,
    )
    SkirmishSpoilFactory(
        skirmish=skirmish,
        faction=skirmish.attacking_faction,
        kind=SkirmishSpoil.KindChoices.KIND_QUEST_REWARD,
        amount=400,
        description="Silence the raiders",
    )

    report = SkirmishReport.for_skirmish(skirmish=skirmish, faction=skirmish.attacking_faction)

    assert (report.silver_looted, report.quest_reward, report.silver_won) == (12, 400, 412)
    assert report.quest_name == "Silence the raiders"


@pytest.mark.django_db
def test_silver_lost_counts_the_purses_taken_from_the_faction_s_own_fallen():
    skirmish = SkirmishFactory()
    own_warrior = WarriorFactory(faction=skirmish.attacking_faction)
    skirmish.attacking_warriors.add(own_warrior)
    SkirmishSpoilFactory(
        skirmish=skirmish,
        faction=skirmish.defending_faction,
        kind=SkirmishSpoil.KindChoices.KIND_SILVER_LOOTED,
        amount=9,
        warrior=own_warrior,
    )

    report = SkirmishReport.for_skirmish(skirmish=skirmish, faction=skirmish.attacking_faction)

    assert report.silver_lost == 9


@pytest.mark.django_db
def test_a_fight_that_yielded_nothing_says_so():
    skirmish = SkirmishFactory()

    report = SkirmishReport.for_skirmish(skirmish=skirmish, faction=skirmish.attacking_faction)

    assert report.has_anything_to_report is False
    assert report.quest_name == ""


@pytest.mark.django_db
def test_a_fight_that_yielded_only_silver_still_has_something_to_report():
    skirmish = SkirmishFactory()
    SkirmishSpoilFactory(
        skirmish=skirmish,
        faction=skirmish.attacking_faction,
        kind=SkirmishSpoil.KindChoices.KIND_SILVER_LOOTED,
        amount=7,
    )

    report = SkirmishReport.for_skirmish(skirmish=skirmish, faction=skirmish.attacking_faction)

    assert report.has_anything_to_report is True
