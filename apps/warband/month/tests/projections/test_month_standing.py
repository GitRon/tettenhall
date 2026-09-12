import pytest

from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.item.tests.factories.item import ItemFactory
from apps.warband.month.projections.month_standing import MonthStanding, WarbandStanding
from apps.warband.quest.tests.factories.quest import QuestFactory
from apps.warband.savegame.models.savegame import Savegame
from apps.warband.savegame.tests.factories.savegame import SavegameFactory
from apps.warband.skirmish.models import Warrior
from apps.warband.skirmish.tests.factories.skirmish import SkirmishFactory
from apps.warband.skirmish.tests.factories.warrior import WarriorFactory
from apps.warband.town.tests.factories.town import TownFactory


def test_is_intact_is_true_while_every_man_left_is_fit():
    warband = WarbandStanding(
        warrior_count=3,
        unconscious_count=0,
        fleeing_count=0,
        leader=None,
        leader_can_march=False,
        fyrd_reserve=0,
        captive_count=0,
    )

    assert warband.is_intact is True


def test_is_intact_is_false_with_a_man_still_routed():
    warband = WarbandStanding(
        warrior_count=3,
        unconscious_count=0,
        fleeing_count=1,
        leader=None,
        leader_can_march=False,
        fyrd_reserve=0,
        captive_count=0,
    )

    assert warband.is_intact is False


def test_is_intact_is_false_with_a_man_down():
    warband = WarbandStanding(
        warrior_count=3,
        unconscious_count=1,
        fleeing_count=0,
        leader=None,
        leader_can_march=False,
        fyrd_reserve=0,
        captive_count=0,
    )

    assert warband.is_intact is False


@pytest.mark.django_db
def test_for_savegame_answers_none_without_a_player_faction():
    """
    A reachable state and not a contrived one: the savegame row is written before its faction is, and
    the page it lands on is this one.
    """
    savegame = SavegameFactory(player_faction=None)

    assert MonthStanding.for_savegame(savegame=savegame) is None


@pytest.mark.django_db
def test_open_skirmish_count_counts_the_fights_blocking_the_month():
    """
    A decided fight does not block anything, so counting every skirmish of the savegame would put a
    permanent warning on the page from the first battle onwards.
    """
    savegame = SavegameFactory()
    player_faction = FactionFactory(savegame=savegame)
    savegame.player_faction = player_faction
    savegame.save()
    SkirmishFactory(attacking_faction=player_faction)
    SkirmishFactory(attacking_faction=player_faction, victorious_faction=player_faction)

    standing = MonthStanding.for_savegame(savegame=savegame)

    assert standing.open_skirmish_count == 1
    assert standing.has_anything_open is True


@pytest.mark.django_db
def test_quest_count_counts_only_the_quests_that_can_still_be_taken_on():
    """
    Through the same queryset the town square offers cards from, so the dashboard cannot promise a
    quest the board then refuses: a target with nobody left to defend it is no quest at all.
    """
    savegame = SavegameFactory()
    player_faction = FactionFactory(savegame=savegame)
    savegame.player_faction = player_faction
    savegame.save()
    defended_target = FactionFactory(savegame=savegame)
    WarriorFactory(faction=defended_target)
    player_faction.available_quests.add(
        QuestFactory(target_faction=defended_target),
        QuestFactory(target_faction=FactionFactory(savegame=savegame)),
    )

    standing = MonthStanding.for_savegame(savegame=savegame)

    assert standing.quest_count == 1


@pytest.mark.django_db
def test_attackable_rival_list_names_the_rivals_a_war_band_may_march_on():
    """
    Named rather than counted, and asked through the queryset the attack view resolves its target
    with - a rival offered here that the attack then refuses is worse than offering nobody.
    """
    savegame = SavegameFactory()
    player_faction = FactionFactory(savegame=savegame)
    player_faction.leader = WarriorFactory(faction=player_faction)
    player_faction.save()
    savegame.player_faction = player_faction
    savegame.save()
    rival = FactionFactory(savegame=savegame, name="Hwicce")
    WarriorFactory(faction=rival)
    FactionFactory(savegame=savegame, name="Magonsaete")

    standing = MonthStanding.for_savegame(savegame=savegame)

    assert standing.attackable_rival_list == [rival]


@pytest.mark.django_db
def test_occupiable_rival_list_names_the_towns_left_standing_empty():
    savegame = SavegameFactory()
    player_faction = FactionFactory(savegame=savegame)
    player_faction.leader = WarriorFactory(faction=player_faction)
    player_faction.save()
    savegame.player_faction = player_faction
    savegame.save()
    emptied_rival = FactionFactory(savegame=savegame, name="Hwicce")
    emptied_rival.leader = WarriorFactory(faction=emptied_rival, condition=Warrior.ConditionChoices.CONDITION_DEAD)
    emptied_rival.save()

    standing = MonthStanding.for_savegame(savegame=savegame)

    assert standing.occupiable_rival_list == [emptied_rival]


@pytest.mark.django_db
def test_can_build_is_false_once_a_building_has_been_raised_this_month():
    savegame = SavegameFactory(current_month=4)
    player_faction = FactionFactory(savegame=savegame, town__last_constructed_building_at=4)
    savegame.player_faction = player_faction
    savegame.save()

    standing = MonthStanding.for_savegame(savegame=savegame)

    assert standing.can_build is False


@pytest.mark.django_db
def test_can_build_is_true_while_the_month_has_seen_no_building():
    savegame = SavegameFactory(current_month=4)
    player_faction = FactionFactory(savegame=savegame, town__last_constructed_building_at=3)
    savegame.player_faction = player_faction
    savegame.save()

    standing = MonthStanding.for_savegame(savegame=savegame)

    assert standing.can_build is True


@pytest.mark.django_db
def test_building_income_reads_the_hall_the_town_has_standing():
    savegame = SavegameFactory()
    player_faction = FactionFactory(savegame=savegame, town=None)
    TownFactory(faction=player_faction, hall=1)
    WarriorFactory(faction=player_faction, monthly_salary=100)
    savegame.player_faction = player_faction
    savegame.save()

    standing = MonthStanding.for_savegame(savegame=savegame)

    assert standing.building_income == 300


@pytest.mark.django_db
def test_building_income_pays_the_share_of_an_under_manned_hall():
    """
    The dashboard counts the men the month counts. A hall pays a share while the war band is short
    of it, and a page promising the full revenue would name a figure the month then does not pay.
    """
    savegame = SavegameFactory()
    player_faction = FactionFactory(savegame=savegame, town=None)
    TownFactory(faction=player_faction, hall=1)
    savegame.player_faction = player_faction
    savegame.save()

    standing = MonthStanding.for_savegame(savegame=savegame)

    assert standing.building_income == 50


@pytest.mark.django_db
def test_building_income_is_nil_for_a_faction_that_has_no_town_yet():
    """
    A town is created together with its faction, so this is a guard rather than a state a player
    reaches - without it the first page a half-built savegame lands on answers 500.
    """
    savegame = SavegameFactory()
    player_faction = FactionFactory(savegame=savegame, town=None)
    savegame.player_faction = player_faction
    savegame.save()

    standing = MonthStanding.for_savegame(savegame=savegame)

    assert standing.building_income == 0
    assert standing.can_build is False


@pytest.mark.django_db
def test_shop_item_count_and_pub_mercenary_count_read_the_town_the_player_owns():
    savegame = SavegameFactory()
    player_faction = FactionFactory(savegame=savegame)
    savegame.player_faction = player_faction
    savegame.save()
    player_faction.available_items.add(ItemFactory(savegame=savegame))
    player_faction.available_mercenaries.add(
        WarriorFactory(faction=None, savegame=savegame, culture=player_faction.culture)
    )

    standing = MonthStanding.for_savegame(savegame=savegame)

    assert standing.shop_item_count == 1
    assert standing.pub_mercenary_count == 1


@pytest.mark.django_db
def test_has_anything_open_is_false_on_a_month_with_nothing_left_in_it():
    """
    The one state that earns the page a different sentence rather than an empty panel, and it takes
    an empty shop, an empty pub, a spent building slot and no rival anybody can be marched on.
    """
    savegame = SavegameFactory(current_month=4)
    player_faction = FactionFactory(savegame=savegame, town__last_constructed_building_at=4)
    savegame.player_faction = player_faction
    savegame.save()

    standing = MonthStanding.for_savegame(savegame=savegame)

    assert standing.has_anything_open is False


@pytest.mark.django_db
def test_has_anything_open_is_false_once_the_game_has_been_decided():
    """
    The offers hold that guard themselves, so a decided savegame reaches the same answer as a spent
    month - which is what makes the view's own check about the panels and not about the rules.
    """
    savegame = SavegameFactory(current_month=4, outcome=Savegame.OutcomeChoices.OUTCOME_WON)
    player_faction = FactionFactory(savegame=savegame, town__last_constructed_building_at=4)
    player_faction.leader = WarriorFactory(faction=player_faction)
    player_faction.save()
    savegame.player_faction = player_faction
    savegame.save()
    WarriorFactory(faction=FactionFactory(savegame=savegame))

    standing = MonthStanding.for_savegame(savegame=savegame)

    assert standing.has_anything_open is False


@pytest.mark.django_db
def test_warband_counts_the_living_by_condition():
    """
    The dead are left out the way the roster and the navbar leave them out: a man who is gone is not
    a man in poor condition, and counting him would make the summary disagree with both.
    """
    savegame = SavegameFactory()
    player_faction = FactionFactory(savegame=savegame)
    savegame.player_faction = player_faction
    savegame.save()
    WarriorFactory(faction=player_faction)
    WarriorFactory(faction=player_faction, condition=Warrior.ConditionChoices.CONDITION_UNCONSCIOUS)
    WarriorFactory(faction=player_faction, condition=Warrior.ConditionChoices.CONDITION_FLEEING)
    WarriorFactory(faction=player_faction, condition=Warrior.ConditionChoices.CONDITION_DEAD)

    standing = MonthStanding.for_savegame(savegame=savegame)

    assert standing.warband.warrior_count == 3
    assert standing.warband.is_intact is False


@pytest.mark.django_db
def test_warband_counts_only_the_men_of_the_player_faction():
    """
    Every faction of the savegame keeps a roster, so scoping to the savegame would count the rivals'
    men into the player's own summary.
    """
    savegame = SavegameFactory()
    player_faction = FactionFactory(savegame=savegame)
    savegame.player_faction = player_faction
    savegame.save()
    WarriorFactory(faction=player_faction)
    WarriorFactory(faction=FactionFactory(savegame=savegame))

    standing = MonthStanding.for_savegame(savegame=savegame)

    assert standing.warband.warrior_count == 1


@pytest.mark.django_db
def test_warband_leader_can_march_while_he_is_fit_and_free():
    savegame = SavegameFactory()
    player_faction = FactionFactory(savegame=savegame)
    leader = WarriorFactory(faction=player_faction)
    player_faction.leader = leader
    player_faction.save()
    savegame.player_faction = player_faction
    savegame.save()

    standing = MonthStanding.for_savegame(savegame=savegame)

    assert standing.warband.leader == leader
    assert standing.warband.leader_can_march is True


@pytest.mark.django_db
def test_warband_leader_cannot_march_once_he_is_down():
    """
    The answer the player can only get today by opening a rival's page and reading the footnote that
    explains the missing Attack button.
    """
    savegame = SavegameFactory()
    player_faction = FactionFactory(savegame=savegame)
    player_faction.leader = WarriorFactory(
        faction=player_faction, condition=Warrior.ConditionChoices.CONDITION_UNCONSCIOUS
    )
    player_faction.save()
    savegame.player_faction = player_faction
    savegame.save()

    standing = MonthStanding.for_savegame(savegame=savegame)

    assert standing.warband.leader_can_march is False


@pytest.mark.django_db
def test_warband_has_no_leader_before_one_is_appointed():
    savegame = SavegameFactory()
    player_faction = FactionFactory(savegame=savegame, leader=None)
    savegame.player_faction = player_faction
    savegame.save()

    standing = MonthStanding.for_savegame(savegame=savegame)

    assert standing.warband.leader is None
    assert standing.warband.leader_can_march is False


@pytest.mark.django_db
def test_warband_reads_the_fyrd_and_the_captives_off_the_faction():
    savegame = SavegameFactory()
    player_faction = FactionFactory(savegame=savegame, fyrd_reserve=7)
    savegame.player_faction = player_faction
    savegame.save()
    player_faction.captured_warriors.add(
        WarriorFactory(faction=None, savegame=savegame, culture=player_faction.culture)
    )

    standing = MonthStanding.for_savegame(savegame=savegame)

    assert standing.warband.fyrd_reserve == 7
    assert standing.warband.captive_count == 1
