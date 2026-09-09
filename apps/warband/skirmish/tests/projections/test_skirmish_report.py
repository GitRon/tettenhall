import pytest

from apps.warband.item.models.item_type import ItemType
from apps.warband.item.tests.factories.item import ItemFactory
from apps.warband.item.tests.factories.item_type import ItemTypeFactory
from apps.warband.skirmish.models.skirmish_casualty import SkirmishCasualty
from apps.warband.skirmish.models.skirmish_spoil import SkirmishSpoil
from apps.warband.skirmish.projections.skirmish_report import SkirmishReport
from apps.warband.skirmish.tests.factories.skirmish import SkirmishFactory
from apps.warband.skirmish.tests.factories.skirmish_casualty import SkirmishCasualtyFactory
from apps.warband.skirmish.tests.factories.skirmish_spoil import SkirmishSpoilFactory
from apps.warband.skirmish.tests.factories.skirmish_warrior_growth import SkirmishWarriorGrowthFactory
from apps.warband.skirmish.tests.factories.warrior import WarriorFactory


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


@pytest.mark.django_db
def test_own_casualties_names_the_faction_s_own_dead():
    skirmish = SkirmishFactory()
    own_warrior = WarriorFactory(faction=skirmish.attacking_faction)
    skirmish.attacking_warriors.add(own_warrior)
    casualty = SkirmishCasualtyFactory(
        skirmish=skirmish, warrior=own_warrior, fate=SkirmishCasualty.FateChoices.FATE_KILLED
    )

    report = SkirmishReport.for_skirmish(skirmish=skirmish, faction=skirmish.attacking_faction)

    assert report.own_casualties == [casualty]
    assert report.has_anything_to_report is True


@pytest.mark.django_db
def test_own_casualties_names_a_man_taken_prisoner_in_this_very_fight():
    """
    A capture clears the warrior's faction, so reading it would hand the player's own man to the
    enemy's column. The roster is what still knows whose he was.
    """
    skirmish = SkirmishFactory()
    own_warrior = WarriorFactory(faction=skirmish.attacking_faction)
    skirmish.attacking_warriors.add(own_warrior)
    casualty = SkirmishCasualtyFactory(
        skirmish=skirmish, warrior=own_warrior, fate=SkirmishCasualty.FateChoices.FATE_CAPTURED
    )
    own_warrior.faction = None
    own_warrior.save()

    report = SkirmishReport.for_skirmish(skirmish=skirmish, faction=skirmish.attacking_faction)

    assert report.own_casualties == [casualty]


@pytest.mark.django_db
def test_own_casualties_names_a_man_merely_knocked_out_on_the_winning_side():
    """
    He keeps his gear and his place on the roster, so the fate is what says he is not a loss - but
    he was out of the fight, and the panel accounts for him.
    """
    skirmish = SkirmishFactory()
    own_warrior = WarriorFactory(faction=skirmish.attacking_faction)
    skirmish.attacking_warriors.add(own_warrior)
    casualty = SkirmishCasualtyFactory(
        skirmish=skirmish, warrior=own_warrior, fate=SkirmishCasualty.FateChoices.FATE_INCAPACITATED
    )

    report = SkirmishReport.for_skirmish(skirmish=skirmish, faction=skirmish.attacking_faction)

    assert report.own_casualties == [casualty]
    assert casualty.get_fate_display() == "Knocked unconscious"


@pytest.mark.django_db
def test_own_casualties_reports_a_man_who_fell_carrying_nothing():
    """
    The case with no spoil row at all: no weapon, no armour and a zero purse. The panel used to
    print "the fight yielded nothing" over him.
    """
    skirmish = SkirmishFactory()
    own_warrior = WarriorFactory(faction=skirmish.attacking_faction)
    skirmish.attacking_warriors.add(own_warrior)
    SkirmishCasualtyFactory(skirmish=skirmish, warrior=own_warrior, fate=SkirmishCasualty.FateChoices.FATE_KILLED)

    report = SkirmishReport.for_skirmish(skirmish=skirmish, faction=skirmish.attacking_faction)

    assert report.has_anything_to_report is True
    assert (report.items_won, report.items_lost, report.silver_won) == ([], [], 0)


@pytest.mark.django_db
def test_own_routed_is_kept_apart_from_the_casualties():
    skirmish = SkirmishFactory()
    own_warrior = WarriorFactory(faction=skirmish.attacking_faction)
    skirmish.attacking_warriors.add(own_warrior)
    routed = SkirmishCasualtyFactory(
        skirmish=skirmish, warrior=own_warrior, fate=SkirmishCasualty.FateChoices.FATE_FLED
    )

    report = SkirmishReport.for_skirmish(skirmish=skirmish, faction=skirmish.attacking_faction)

    assert (report.own_routed, report.own_casualties) == ([routed], [])
    assert report.has_anything_to_report is True


@pytest.mark.django_db
def test_a_won_fight_does_not_file_the_faction_s_own_dead_mans_gear_as_booty():
    """
    His gear and purse go to the victor, who is his own faction, so they arrived as gains off a man
    on the roster. That is the stash getting its kit back - not booty, and not a loss either.
    """
    skirmish = SkirmishFactory()
    own_dead = WarriorFactory(faction=skirmish.attacking_faction)
    skirmish.attacking_warriors.add(own_dead)
    skirmish.victorious_faction = skirmish.attacking_faction
    skirmish.save()
    SkirmishSpoilFactory(
        skirmish=skirmish,
        faction=skirmish.attacking_faction,
        kind=SkirmishSpoil.KindChoices.KIND_ITEM_TAKEN,
        item=ItemFactory(savegame=skirmish.attacking_faction.savegame),
        warrior=own_dead,
    )
    SkirmishSpoilFactory(
        skirmish=skirmish,
        faction=skirmish.attacking_faction,
        kind=SkirmishSpoil.KindChoices.KIND_SILVER_LOOTED,
        amount=9,
        warrior=own_dead,
    )
    SkirmishCasualtyFactory(skirmish=skirmish, warrior=own_dead, fate=SkirmishCasualty.FateChoices.FATE_KILLED)

    report = SkirmishReport.for_skirmish(skirmish=skirmish, faction=skirmish.attacking_faction)

    assert (report.items_won, report.silver_looted) == ([], 0)
    assert (report.items_lost, report.silver_lost) == ([], 0)


@pytest.mark.django_db
def test_prisoners_taken_names_the_enemy_and_not_the_captor_s_own_downed_men():
    skirmish = SkirmishFactory()
    own_downed = WarriorFactory(faction=skirmish.attacking_faction)
    skirmish.attacking_warriors.add(own_downed)
    enemy = WarriorFactory(faction=skirmish.defending_faction)
    skirmish.defending_warriors.add(enemy)
    SkirmishCasualtyFactory(skirmish=skirmish, warrior=own_downed, fate=SkirmishCasualty.FateChoices.FATE_INCAPACITATED)
    prisoner = SkirmishCasualtyFactory(
        skirmish=skirmish, warrior=enemy, fate=SkirmishCasualty.FateChoices.FATE_CAPTURED
    )

    report = SkirmishReport.for_skirmish(skirmish=skirmish, faction=skirmish.attacking_faction)

    assert report.prisoners_taken == [prisoner]
    assert report.own_casualties == [SkirmishCasualty.objects.get(warrior=own_downed)]


@pytest.mark.django_db
def test_the_enemy_s_dead_are_counted_and_told_apart_from_the_ones_merely_left_lying():
    """
    The overkill threshold decides which, and the report says which happened without naming eight
    men over the two of the player's own that matter.
    """
    skirmish = SkirmishFactory()
    skirmish.defending_warriors.add(WarriorFactory(faction=skirmish.defending_faction))
    SkirmishCasualtyFactory(
        skirmish=skirmish,
        warrior=WarriorFactory(faction=skirmish.defending_faction),
        fate=SkirmishCasualty.FateChoices.FATE_KILLED,
    )
    SkirmishCasualtyFactory(
        skirmish=skirmish,
        warrior=WarriorFactory(faction=skirmish.defending_faction),
        fate=SkirmishCasualty.FateChoices.FATE_INCAPACITATED,
    )

    report = SkirmishReport.for_skirmish(skirmish=skirmish, faction=skirmish.attacking_faction)

    assert (report.enemy_killed_count, report.enemy_downed_count) == (1, 1)
    assert report.has_anything_to_report is True


@pytest.mark.django_db
def test_a_fight_the_faction_lost_nobody_in_reports_no_casualties():
    skirmish = SkirmishFactory()
    own_warrior = WarriorFactory(faction=skirmish.attacking_faction)
    skirmish.attacking_warriors.add(own_warrior)

    report = SkirmishReport.for_skirmish(skirmish=skirmish, faction=skirmish.attacking_faction)

    assert (report.own_casualties, report.own_routed, report.prisoners_taken) == ([], [], [])
    assert (report.enemy_killed_count, report.enemy_downed_count) == (0, 0)
