from unittest import mock

import pytest

from apps.faker_frisian import FRISIAN_BASE_LOCALE, FRISIAN_LOCALE
from apps.warband.faction.domain.fyrd_reserve import FyrdReserve
from apps.warband.faction.handlers.commands.faction import (
    _create_faction,
    handle_change_fyrd_reserve,
    handle_create_factions_for_new_savegame,
    handle_defeat_faction_of_lost_leader,
    handle_earn_money_from_buildings,
    handle_occupy_faction,
    handle_plan_faction_month,
    handle_prepare_faction_warriors_for_month,
    handle_replenish_fyrd_reserve,
)
from apps.warband.faction.messages.commands.faction import (
    ChangeFyrdReserve,
    CreateFactionsForNewSavegame,
    DefeatFactionOfLostLeader,
    EarnMoneyFromBuildings,
    OccupyFaction,
    PlanFactionMonth,
    PrepareFactionWarriorsForMonth,
    ReplenishFyrdReserve,
)
from apps.warband.faction.messages.events.faction import (
    FactionFyrdReserveReplenished,
    FactionLeaderRaisedFromFyrd,
    FactionLeaderSucceeded,
    FactionMonthPlanned,
    FactionWasDefeated,
    FactionWasOccupied,
    FyrdReserveChanged,
    MonthlyBuildingMoneyEarned,
    NewFactionCreated,
    TownBuildingUpgradeApproved,
)
from apps.warband.faction.messages.events.item import ShopItemPurchaseApproved
from apps.warband.faction.messages.events.warrior import (
    FyrdDraftApproved,
    PubMercenaryHireApproved,
    WarriorMonthPrepared,
    WarriorRecruited,
)
from apps.warband.faction.models.culture import Culture
from apps.warband.faction.models.faction import Faction
from apps.warband.faction.tests.factories.culture import CultureFactory
from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.finance.tests.factories.transaction import TransactionFactory
from apps.warband.item.models.item_type import ItemType
from apps.warband.item.tests.factories.item import ItemFactory
from apps.warband.item.tests.factories.item_type import ItemTypeFactory
from apps.warband.savegame.tests.factories.savegame import SavegameFactory
from apps.warband.skirmish.models.warrior import Warrior
from apps.warband.skirmish.tests.factories.warrior import WarriorFactory
from apps.warband.town.models import Town


@pytest.mark.django_db
def test_create_faction_for_player_faction():
    savegame = SavegameFactory(current_month=5)
    culture = CultureFactory()

    with mock.patch.object(FyrdReserve, "roll_starting_reserve", return_value=4):
        result = _create_faction(
            name="Wessex",
            town_name="Winchester",
            culture_id=culture.id,
            savegame=savegame,
            is_player=True,
        )

    assert result == Faction.objects.get(name="Wessex")
    savegame.refresh_from_db()
    assert (savegame.player_faction, result.town_name) == (result, "Winchester")


@pytest.mark.django_db
def test_create_faction_for_a_rival():
    savegame = SavegameFactory(current_month=5)
    culture = CultureFactory()

    with mock.patch.object(FyrdReserve, "roll_starting_reserve", return_value=4):
        result = _create_faction(
            name="Mercia",
            town_name="Tamworth",
            culture_id=culture.id,
            savegame=savegame,
            is_player=False,
        )

    assert result.fyrd_reserve == 4
    savegame.refresh_from_db()
    assert savegame.player_faction is None


@pytest.mark.django_db
def test_create_faction_gives_the_player_a_town_at_every_default():
    """
    Months count from 1, so "last_constructed_building_at" at 0 is what leaves month 1 buildable.
    """
    savegame = SavegameFactory(current_month=5)

    result = _create_faction(
        name="Wessex",
        town_name="Winchester",
        culture_id=CultureFactory().id,
        savegame=savegame,
        is_player=True,
    )

    town = result.town
    assert (town.hall, town.weaponsmith, town.marketplace, town.sanctuary, town.fortification) == (0, 0, 0, 0, 0)
    assert town.last_constructed_building_at == 0


@pytest.mark.django_db
def test_create_faction_gives_a_rival_a_chosen_sanctuary_and_wall():
    """
    A rival raises only its hall, so the levels it is created with are the pace its wounded mend at and
    the wall the player meets for the rest of the savegame. The other three buildings stay at 0 on
    purpose, and the hall starts where the player's does.
    """
    savegame = SavegameFactory(current_month=5)

    result = _create_faction(
        name="Mercia",
        town_name="Tamworth",
        culture_id=CultureFactory().id,
        savegame=savegame,
        is_player=False,
    )

    town = result.town
    assert (town.sanctuary, town.fortification) == (
        Town.SanctuaryChoices.SANCTUARY_SMALL,
        Town.FortificationChoices.FORTIFICATION_SMALL,
    )
    assert (town.hall, town.weaponsmith, town.marketplace) == (0, 0, 0)


@pytest.mark.django_db
def test_handle_defeat_faction_of_lost_leader_knocks_the_faction_out():
    """Nobody on the roster and nobody left in the fyrd: there is no one to take the seat."""
    player_faction = FactionFactory()
    savegame = player_faction.savegame
    savegame.player_faction = player_faction
    savegame.current_month = 4
    savegame.save()
    faction = FactionFactory(savegame=savegame, fyrd_reserve=0)
    leader = WarriorFactory(faction=faction, savegame=savegame, condition=Warrior.ConditionChoices.CONDITION_DEAD)
    faction.leader = leader
    faction.save()

    result = handle_defeat_faction_of_lost_leader(context=DefeatFactionOfLostLeader(warrior=leader))

    assert result == FactionWasDefeated(
        faction=faction,
        savegame=savegame,
        player_faction=player_faction,
        leader=leader,
        leader_was_killed=True,
        month=4,
    )
    faction.refresh_from_db()
    assert faction.is_defeated is True


@pytest.mark.django_db
def test_handle_defeat_faction_of_lost_leader_for_a_captured_leader():
    """
    Capture clears the warrior's own faction before this runs, so the lookup has to go through
    Faction.leader - the only remaining record of who led whom.

    A captured man is knocked out and taken rather than killed, which is what tells the announcement
    to call him a prisoner instead of one of the fallen.
    """
    player_faction = FactionFactory()
    savegame = player_faction.savegame
    savegame.player_faction = player_faction
    savegame.save()
    faction = FactionFactory(savegame=savegame, fyrd_reserve=0)
    leader = WarriorFactory(
        faction=faction, savegame=savegame, condition=Warrior.ConditionChoices.CONDITION_UNCONSCIOUS
    )
    faction.leader = leader
    faction.save()
    leader.faction = None
    leader.save()

    result = handle_defeat_faction_of_lost_leader(context=DefeatFactionOfLostLeader(warrior=leader))

    assert result == FactionWasDefeated(
        faction=faction,
        savegame=savegame,
        player_faction=player_faction,
        leader=leader,
        leader_was_killed=False,
        month=1,
    )


def _rival_led_by_a_fallen_leader(*, fyrd_reserve: int = 0) -> tuple[Faction, Faction, Warrior]:
    """The fyrd is empty unless asked for, so a roster with nobody on it knocks the rival out."""
    player_faction = FactionFactory()
    savegame = player_faction.savegame
    savegame.player_faction = player_faction
    savegame.current_month = 4
    savegame.save()
    faction = FactionFactory(savegame=savegame, fyrd_reserve=fyrd_reserve)
    leader = WarriorFactory(faction=faction, savegame=savegame, condition=Warrior.ConditionChoices.CONDITION_DEAD)
    faction.leader = leader
    faction.save()

    return player_faction, faction, leader


@pytest.mark.django_db
def test_handle_defeat_faction_of_lost_leader_seats_the_man_with_the_most_renown():
    player_faction, faction, leader = _rival_led_by_a_fallen_leader()
    WarriorFactory(faction=faction, savegame=faction.savegame, renown=5, experience=900)
    successor = WarriorFactory(
        faction=faction, savegame=faction.savegame, renown=20, condition=Warrior.ConditionChoices.CONDITION_UNCONSCIOUS
    )

    result = handle_defeat_faction_of_lost_leader(context=DefeatFactionOfLostLeader(warrior=leader))

    assert result == FactionLeaderSucceeded(
        faction=faction,
        player_faction=player_faction,
        fallen_leader=leader,
        successor=successor,
        leader_was_killed=True,
        month=4,
    )
    faction.refresh_from_db()
    assert (faction.leader, faction.is_defeated) == (successor, False)


@pytest.mark.django_db
def test_handle_defeat_faction_of_lost_leader_settles_a_tie_on_experience():
    _, faction, leader = _rival_led_by_a_fallen_leader()
    WarriorFactory(faction=faction, savegame=faction.savegame, renown=10, experience=100)
    successor = WarriorFactory(faction=faction, savegame=faction.savegame, renown=10, experience=300)

    handle_defeat_faction_of_lost_leader(context=DefeatFactionOfLostLeader(warrior=leader))

    faction.refresh_from_db()
    assert faction.leader == successor


@pytest.mark.django_db
def test_handle_defeat_faction_of_lost_leader_passes_over_the_dead():
    _, faction, leader = _rival_led_by_a_fallen_leader()
    WarriorFactory(faction=faction, savegame=faction.savegame, condition=Warrior.ConditionChoices.CONDITION_DEAD)

    result = handle_defeat_faction_of_lost_leader(context=DefeatFactionOfLostLeader(warrior=leader))

    assert isinstance(result, FactionWasDefeated)


@pytest.mark.django_db
def test_handle_defeat_faction_of_lost_leader_seats_a_successor_for_the_player_too():
    """
    The same rule for both sides: the player's savegame goes on while he has a man left.
    """
    player_faction = FactionFactory()
    savegame = player_faction.savegame
    savegame.player_faction = player_faction
    savegame.save()
    leader = WarriorFactory(
        faction=player_faction, savegame=savegame, condition=Warrior.ConditionChoices.CONDITION_DEAD
    )
    player_faction.leader = leader
    player_faction.save()
    successor = WarriorFactory(faction=player_faction, savegame=savegame)

    result = handle_defeat_faction_of_lost_leader(context=DefeatFactionOfLostLeader(warrior=leader))

    assert result == FactionLeaderSucceeded(
        faction=player_faction,
        player_faction=player_faction,
        fallen_leader=leader,
        successor=successor,
        leader_was_killed=True,
        month=1,
    )


@pytest.mark.django_db
def test_handle_defeat_faction_of_lost_leader_for_an_occupation_knocks_the_faction_out_anyway():
    """Neither the man on the roster nor the fyrd behind him saves a town that has been taken."""
    _, faction, leader = _rival_led_by_a_fallen_leader(fyrd_reserve=3)
    WarriorFactory(faction=faction, savegame=faction.savegame, renown=20)

    result = handle_defeat_faction_of_lost_leader(
        context=DefeatFactionOfLostLeader(warrior=leader, allow_succession=False)
    )

    assert isinstance(result, FactionWasDefeated)
    faction.refresh_from_db()
    assert (faction.leader, faction.is_defeated) == (leader, True)


@pytest.mark.django_db
def test_handle_defeat_faction_of_lost_leader_raises_a_leader_from_the_fyrd():
    """
    Nobody is left on the roster, but the fyrd has two men: one of them takes the seat, and comes with
    the recruitment the hand-out arms him off.
    """
    player_faction, faction, leader = _rival_led_by_a_fallen_leader(fyrd_reserve=2)

    result = handle_defeat_faction_of_lost_leader(context=DefeatFactionOfLostLeader(warrior=leader))

    faction.refresh_from_db()
    assert result == [
        FactionLeaderRaisedFromFyrd(
            faction=faction,
            player_faction=player_faction,
            fallen_leader=leader,
            successor=faction.leader,
            leader_was_killed=True,
            month=4,
        ),
        WarriorRecruited(faction=faction, warrior=faction.leader, recruitment_price=0, month=4),
    ]
    assert (faction.leader.faction, faction.fyrd_reserve, faction.is_defeated) == (faction, 1, False)


@pytest.mark.django_db
def test_handle_defeat_faction_of_lost_leader_raises_a_leader_from_the_fyrd_for_the_player_too():
    player_faction = FactionFactory(fyrd_reserve=1)
    savegame = player_faction.savegame
    savegame.player_faction = player_faction
    savegame.save()
    leader = WarriorFactory(
        faction=player_faction, savegame=savegame, condition=Warrior.ConditionChoices.CONDITION_DEAD
    )
    player_faction.leader = leader
    player_faction.save()

    handle_defeat_faction_of_lost_leader(context=DefeatFactionOfLostLeader(warrior=leader))

    player_faction.refresh_from_db()
    assert (player_faction.leader != leader, player_faction.fyrd_reserve, player_faction.is_defeated) == (
        True,
        0,
        False,
    )


@pytest.mark.django_db
def test_handle_defeat_faction_of_lost_leader_for_an_ordinary_warrior():
    faction = FactionFactory()
    warrior = WarriorFactory(faction=faction, savegame=faction.savegame)

    result = handle_defeat_faction_of_lost_leader(context=DefeatFactionOfLostLeader(warrior=warrior))

    assert result is None


@pytest.mark.django_db
def test_handle_defeat_faction_of_lost_leader_for_an_already_defeated_faction():
    """
    Reachable: the leader can be killed in the fight and then captured when it is resolved.
    """
    faction = FactionFactory(is_defeated=True)
    leader = WarriorFactory(faction=faction, savegame=faction.savegame)
    faction.leader = leader
    faction.save()

    result = handle_defeat_faction_of_lost_leader(context=DefeatFactionOfLostLeader(warrior=leader))

    assert result is None


@pytest.mark.django_db
def test_handle_replenish_fyrd_reserve_with_new_recruits():
    faction = FactionFactory(fyrd_reserve=3)

    with mock.patch.object(FyrdReserve, "roll_monthly_recruits", return_value=2):
        result = handle_replenish_fyrd_reserve(context=ReplenishFyrdReserve(faction=faction, month=3))

    assert result == FactionFyrdReserveReplenished(faction=faction, new_recruits=2, month=3)
    faction.refresh_from_db()
    assert faction.fyrd_reserve == 5


@pytest.mark.django_db
def test_handle_replenish_fyrd_reserve_without_new_recruits():
    faction = FactionFactory(fyrd_reserve=3)

    with mock.patch.object(FyrdReserve, "roll_monthly_recruits", return_value=0):
        result = handle_replenish_fyrd_reserve(context=ReplenishFyrdReserve(faction=faction, month=3))

    assert result is None
    faction.refresh_from_db()
    assert faction.fyrd_reserve == 3


@pytest.mark.django_db
def test_handle_change_fyrd_reserve_upwards():
    faction = FactionFactory(fyrd_reserve=3)

    result = handle_change_fyrd_reserve(context=ChangeFyrdReserve(faction=faction, change=2, month=3))

    assert result == FyrdReserveChanged(faction=faction, change=2, month=3)
    faction.refresh_from_db()
    assert faction.fyrd_reserve == 5


@pytest.mark.django_db
def test_handle_change_fyrd_reserve_downwards():
    faction = FactionFactory(fyrd_reserve=3)

    result = handle_change_fyrd_reserve(context=ChangeFyrdReserve(faction=faction, change=-2, month=3))

    assert result == FyrdReserveChanged(faction=faction, change=-2, month=3)
    faction.refresh_from_db()
    assert faction.fyrd_reserve == 1


@pytest.mark.django_db
def test_handle_prepare_faction_warriors_for_month_hands_the_month_to_the_roster():
    faction = FactionFactory()
    warrior = WarriorFactory(faction=faction)

    result = handle_prepare_faction_warriors_for_month(context=PrepareFactionWarriorsForMonth(faction=faction, month=3))

    assert result == [WarriorMonthPrepared(faction=faction, warrior=warrior, month=3)]


@pytest.mark.django_db
def test_handle_prepare_faction_warriors_for_month_keeps_a_man_at_full_strength():
    """
    The read is unfiltered on purpose, which is what makes the event a fact rather than an
    announcement that a query returned. Whether anything applies to this man is the reactions' call.
    """
    faction = FactionFactory()
    untouched_warrior = WarriorFactory(
        faction=faction, current_health=20, max_health=20, current_morale=20, max_morale=20
    )

    result = handle_prepare_faction_warriors_for_month(context=PrepareFactionWarriorsForMonth(faction=faction, month=3))

    assert result == [WarriorMonthPrepared(faction=faction, warrior=untouched_warrior, month=3)]


@pytest.mark.django_db
def test_handle_prepare_faction_warriors_for_month_skips_dead_warriors():
    """
    The one filter the read keeps. A month does nothing to a corpse, and every reaction would
    otherwise have to say so for itself.
    """
    faction = FactionFactory()
    WarriorFactory(faction=faction, condition=Warrior.ConditionChoices.CONDITION_DEAD)

    result = handle_prepare_faction_warriors_for_month(context=PrepareFactionWarriorsForMonth(faction=faction, month=3))

    assert result == []


@pytest.mark.django_db
def test_handle_prepare_faction_warriors_for_month_reaches_a_captive_of_this_faction():
    """
    A captive is on nobody's roster, so his captor's month is the only one that can reach him.

    The captor rides along rather than the man's own faction, which capture cleared: it is his
    sanctuary that mends him and his month log the line belongs in.
    """
    captor = FactionFactory()
    captive = WarriorFactory(
        faction=None,
        savegame=captor.savegame,
        culture=captor.culture,
        condition=Warrior.ConditionChoices.CONDITION_UNCONSCIOUS,
    )
    captor.captured_warriors.add(captive)

    result = handle_prepare_faction_warriors_for_month(context=PrepareFactionWarriorsForMonth(faction=captor, month=3))

    assert result == [WarriorMonthPrepared(faction=captor, warrior=captive, month=3)]


@pytest.mark.django_db
def test_handle_prepare_faction_warriors_for_month_leaves_another_factions_captive_alone():
    captor = FactionFactory()
    captive = WarriorFactory(
        faction=None,
        savegame=captor.savegame,
        culture=captor.culture,
        condition=Warrior.ConditionChoices.CONDITION_UNCONSCIOUS,
    )
    captor.captured_warriors.add(captive)
    bystander_faction = FactionFactory(savegame=captor.savegame)

    result = handle_prepare_faction_warriors_for_month(
        context=PrepareFactionWarriorsForMonth(faction=bystander_faction, month=3)
    )

    assert result == []


@pytest.mark.django_db
def test_handle_prepare_faction_warriors_for_month_with_an_empty_roster():
    faction = FactionFactory()

    result = handle_prepare_faction_warriors_for_month(context=PrepareFactionWarriorsForMonth(faction=faction, month=3))

    assert result == []


@pytest.mark.django_db
def test_handle_create_factions_for_new_savegame_starts_with_the_player_faction():
    savegame = SavegameFactory()
    culture = CultureFactory()

    with mock.patch("apps.warband.faction.handlers.commands.faction.random.randint", return_value=3):
        result = handle_create_factions_for_new_savegame(
            context=CreateFactionsForNewSavegame(
                savegame=savegame, faction_name="Wessex", town_name="Winchester", faction_culture_id=culture.id
            )
        )

    assert result[0] == NewFactionCreated(
        faction=Faction.objects.get(name="Wessex"), current_month=savegame.current_month, is_player=True
    )
    savegame.refresh_from_db()
    assert savegame.player_faction == result[0].faction


@pytest.mark.django_db
def test_handle_create_factions_for_new_savegame_announces_no_rival_as_the_player():
    savegame = SavegameFactory()
    culture = CultureFactory()

    with mock.patch("apps.warband.faction.handlers.commands.faction.random.randint", return_value=3):
        result = handle_create_factions_for_new_savegame(
            context=CreateFactionsForNewSavegame(
                savegame=savegame, faction_name="Wessex", town_name="Winchester", faction_culture_id=culture.id
            )
        )

    assert [event.is_player for event in result] == [True, False, False, False]


@pytest.mark.django_db
def test_handle_create_factions_for_new_savegame_adds_the_drawn_number_of_rival_factions():
    savegame = SavegameFactory()
    culture = CultureFactory()

    with mock.patch("apps.warband.faction.handlers.commands.faction.random.randint", return_value=3):
        result = handle_create_factions_for_new_savegame(
            context=CreateFactionsForNewSavegame(
                savegame=savegame, faction_name="Wessex", town_name="Winchester", faction_culture_id=culture.id
            )
        )

    assert len(result) == 4
    # Rival factions get a generated town of their own instead of the player's
    assert result[3].faction.town_name not in ("", "Winchester")


@pytest.mark.django_db
def test_handle_create_factions_for_new_savegame_names_each_rival_in_its_own_culture():
    """
    A rival's warriors are generated from the culture on its own row, so its town has to be named from
    that same culture - otherwise the player rides into a Norse-named town held by Frisians.
    """
    savegame = SavegameFactory()
    norse_rival = CultureFactory(locale="no_NO")
    frisian_rival = CultureFactory(locale=FRISIAN_LOCALE)
    swedish_rival = CultureFactory(locale="sv_SE")

    # Faker is third party and random by nature. Standing it in for a stub that echoes the locale it was
    # built with is the only way to tie a generated name back to the culture it was drawn from; seeding
    # the real one is process-global and would leak into the rest of the session.
    #
    # The Frisian rival echoes its base locale rather than "ofs", which is the factory doing its job:
    # Faker refuses "ofs" and the instance is built on "nl_NL" with the provider added on top.
    with (
        mock.patch.object(FyrdReserve, "roll_starting_reserve", return_value=2),
        mock.patch("apps.warband.faction.handlers.commands.faction.random.randint", return_value=3),
        mock.patch(
            "apps.warband.faction.handlers.commands.faction.random.choice",
            side_effect=[norse_rival, frisian_rival, swedish_rival],
        ),
        mock.patch(
            "apps.warband.faction.services.faker.Faker",
            side_effect=lambda locales: mock.Mock(city=mock.Mock(return_value=f"Town of {locales[0]}")),
        ),
    ):
        result = handle_create_factions_for_new_savegame(
            context=CreateFactionsForNewSavegame(
                savegame=savegame,
                faction_name="Wessex",
                town_name="Winchester",
                faction_culture_id=CultureFactory(locale="da_DK").id,
            )
        )

    assert (result[1].faction.name, result[1].faction.town_name, result[1].faction.culture_id) == (
        "Town of no_NO",
        "Town of no_NO",
        norse_rival.id,
    )
    assert (result[2].faction.name, result[2].faction.town_name, result[2].faction.culture_id) == (
        f"Town of {FRISIAN_BASE_LOCALE}",
        f"Town of {FRISIAN_BASE_LOCALE}",
        frisian_rival.id,
    )


@pytest.mark.django_db
def test_handle_create_factions_for_new_savegame_never_deals_a_rival_the_players_culture():
    """
    A rival on the player's own culture is named by the generator the player's war band is named by,
    so the rivals list came back reading as one people under five flags.
    """
    savegame = SavegameFactory()
    player_culture = CultureFactory(locale="da_DK")

    # Five rivals against the cultures the fixtures ship plus this one, so the draw has every chance
    # to land on the player's and the assertion is not passing by luck of a short pool
    with mock.patch("apps.warband.faction.handlers.commands.faction.random.randint", return_value=5):
        result = handle_create_factions_for_new_savegame(
            context=CreateFactionsForNewSavegame(
                savegame=savegame,
                faction_name="Wessex",
                town_name="Winchester",
                faction_culture_id=player_culture.id,
            )
        )

    rival_culture_ids = {event.faction.culture_id for event in result[1:]}
    assert len(rival_culture_ids) > 0
    assert player_culture.id not in rival_culture_ids


@pytest.mark.django_db
def test_handle_create_factions_for_new_savegame_falls_back_to_the_only_culture_there_is():
    """
    Excluding the player's culture from a table holding nothing else would leave nothing to draw
    from, and a savegame with no rivals in it is worse than a rival sharing the player's people.
    """
    savegame = SavegameFactory()
    only_culture = CultureFactory(locale="da_DK")
    # The reference fixtures ship five, and this is the one path where the table holding a single row
    # is the whole point
    Culture.objects.exclude(id=only_culture.id).delete()

    with mock.patch("apps.warband.faction.handlers.commands.faction.random.randint", return_value=3):
        result = handle_create_factions_for_new_savegame(
            context=CreateFactionsForNewSavegame(
                savegame=savegame,
                faction_name="Wessex",
                town_name="Winchester",
                faction_culture_id=only_culture.id,
            )
        )

    assert {event.faction.culture_id for event in result[1:]} == {only_culture.id}


@pytest.mark.django_db
def test_handle_create_factions_for_new_savegame_without_the_culture():
    """
    Cultures are reference data every environment ships with, so a missing one is a half-seeded
    database rather than bad input, and the handler says so by name.

    A culture id nobody owns rather than an emptied table: the fixtures are loaded once per session,
    and this is the path the crash actually arrives by, since a database without them renders the
    dropdown empty and cannot be submitted at all.
    """
    savegame = SavegameFactory()
    missing_culture_id = Culture.objects.order_by("-id").first().id + 1

    with pytest.raises(RuntimeError, match=f"Culture {missing_culture_id} does not exist"):
        handle_create_factions_for_new_savegame(
            context=CreateFactionsForNewSavegame(
                savegame=savegame,
                faction_name="Wessex",
                town_name="Winchester",
                faction_culture_id=missing_culture_id,
            )
        )


@pytest.mark.django_db
def test_handle_earn_money_from_buildings_pays_the_revenue_of_the_hall():
    # A Great Hall brings in 550 silver a month, to the two men on the payroll it asks for
    faction = FactionFactory(town__hall=2)
    WarriorFactory(faction=faction, monthly_salary=170)
    WarriorFactory(faction=faction, monthly_salary=170)

    result = handle_earn_money_from_buildings(context=EarnMoneyFromBuildings(faction=faction, month=3))

    assert result == MonthlyBuildingMoneyEarned(faction=faction, amount=550, month=3)


@pytest.mark.django_db
def test_handle_earn_money_from_buildings_pays_a_share_to_a_war_band_short_of_the_hall():
    faction = FactionFactory(town__hall=2)
    WarriorFactory(faction=faction, monthly_salary=170)

    result = handle_earn_money_from_buildings(context=EarnMoneyFromBuildings(faction=faction, month=3))

    assert result == MonthlyBuildingMoneyEarned(faction=faction, amount=275, month=3)


@pytest.mark.django_db
def test_handle_earn_money_from_buildings_pays_the_baseline_to_a_faction_of_its_leader_alone():
    """
    #192: a hall bought in month one against a war band of nobody earns what a town with no hall
    earns. The leader draws no wage, so a roster of him alone is a payroll of nobody.
    """
    faction = FactionFactory(town__hall=2)
    WarriorFactory(faction=faction, monthly_salary=0)

    result = handle_earn_money_from_buildings(context=EarnMoneyFromBuildings(faction=faction, month=3))

    assert result == MonthlyBuildingMoneyEarned(faction=faction, amount=50, month=3)


@pytest.mark.django_db
def test_handle_earn_money_from_buildings_without_a_hall():
    faction = FactionFactory()
    WarriorFactory(faction=faction, monthly_salary=170)

    result = handle_earn_money_from_buildings(context=EarnMoneyFromBuildings(faction=faction, month=3))

    # A town without a hall still trickles in a baseline
    assert result == MonthlyBuildingMoneyEarned(faction=faction, amount=50, month=3)


@pytest.mark.django_db
def test_handle_occupy_faction_hands_over_the_leader_and_a_share_of_the_treasury():
    occupying_faction = FactionFactory()
    faction = FactionFactory(savegame=occupying_faction.savegame)
    faction.leader = WarriorFactory(faction=faction)
    faction.save()
    TransactionFactory(faction=faction, amount=800)

    result = handle_occupy_faction(context=OccupyFaction(faction=faction, occupying_faction=occupying_faction, month=3))

    assert result == FactionWasOccupied(
        faction=faction,
        occupying_faction=occupying_faction,
        leader=faction.leader,
        plundered_silver=400,
        month=3,
    )


@pytest.mark.django_db
def test_handle_occupy_faction_of_an_empty_treasury():
    occupying_faction = FactionFactory()
    faction = FactionFactory(savegame=occupying_faction.savegame)
    faction.leader = WarriorFactory(faction=faction)
    faction.save()

    result = handle_occupy_faction(context=OccupyFaction(faction=faction, occupying_faction=occupying_faction, month=3))

    assert result.plundered_silver == 0


@pytest.mark.django_db
def test_handle_replenish_fyrd_reserve_in_the_harvest_month():
    """Month 6 is Haligmonath, whose men are in the fields."""
    faction = FactionFactory(fyrd_reserve=3)

    with mock.patch.object(FyrdReserve, "roll_monthly_recruits", return_value=2):
        result = handle_replenish_fyrd_reserve(context=ReplenishFyrdReserve(faction=faction, month=6))

    assert result is None
    faction.refresh_from_db()
    assert faction.fyrd_reserve == 3


def _rival_with_pub(*, purse: int, salary_list: list[int], fyrd_reserve: int = 0) -> tuple[Faction, list[Warrior]]:
    """
    A rival with an empty roster, this much silver, and one mercenary on its shelf per salary.

    A man who just arrived costs twice his wage - see [Warrior.hiring_price]. The fyrd is empty unless
    asked for, because a rival with free men left in it hires nobody. The hall is built to the top, so
    raising it is not among the things the purse could go on.
    """
    rival_faction = FactionFactory(fyrd_reserve=fyrd_reserve, town__hall=Town.HallChoices.HALL_LARGE)
    TransactionFactory(faction=rival_faction, amount=purse)
    mercenary_list = [
        WarriorFactory(
            faction=None,
            savegame=rival_faction.savegame,
            culture=rival_faction.culture,
            monthly_salary=salary,
            is_pub_stock=True,
        )
        for salary in salary_list
    ]
    rival_faction.available_mercenaries.add(*mercenary_list)

    return rival_faction, mercenary_list


@pytest.mark.django_db
def test_handle_plan_faction_month_drafts_for_a_rival_whose_purse_covers_its_wages():
    rival_faction = FactionFactory(fyrd_reserve=2, town__hall=Town.HallChoices.HALL_LARGE)
    WarriorFactory(faction=rival_faction, monthly_salary=150)
    TransactionFactory(faction=rival_faction, amount=1000)

    result = handle_plan_faction_month(context=PlanFactionMonth(faction=rival_faction, month=3))

    assert result == [
        FyrdDraftApproved(faction=rival_faction, month=3),
        FactionMonthPlanned(faction=rival_faction, month=3),
    ]


@pytest.mark.django_db
def test_handle_plan_faction_month_drafts_nobody_for_a_rival_whose_roster_outweighs_its_purse():
    """
    The wage bill is the roster's, read off the same payroll the salary run bills from: 100 in the
    purse against a man drawing 150 leaves no keep for another.
    """
    rival_faction = FactionFactory(fyrd_reserve=2)
    WarriorFactory(faction=rival_faction, monthly_salary=150)
    TransactionFactory(faction=rival_faction, amount=100)

    result = handle_plan_faction_month(context=PlanFactionMonth(faction=rival_faction, month=3))

    assert result == [FactionMonthPlanned(faction=rival_faction, month=3)]


@pytest.mark.django_db
def test_handle_plan_faction_month_hires_for_a_rival_out_of_its_own_pub():
    """
    The decision comes back keyed by id, and the approval carries the man off the shelf rather than a
    fresh row - his price on the event is read off that instance when his hire drains. The closing
    event comes after him, so the restock it triggers cannot sweep him away first.
    """
    # 1000 less his price of 200 still covers his wage of 100
    rival_faction, [mercenary] = _rival_with_pub(purse=1000, salary_list=[100])

    result = handle_plan_faction_month(context=PlanFactionMonth(faction=rival_faction, month=3))

    assert result == [
        PubMercenaryHireApproved(faction=rival_faction, warrior=mercenary, month=3),
        FactionMonthPlanned(faction=rival_faction, month=3),
    ]


@pytest.mark.django_db
def test_handle_plan_faction_month_reads_the_fyrd_off_the_row():
    """
    The faction on the message still shows the empty fyrd it was loaded with, while the month's
    replenishment has already put a man in it. The row is what counts, so the rival drafts him.
    """
    rival_faction, _ = _rival_with_pub(purse=1000, salary_list=[])
    Faction.objects.filter(id=rival_faction.id).update(fyrd_reserve=1)

    result = handle_plan_faction_month(context=PlanFactionMonth(faction=rival_faction, month=3))

    assert result == [
        FyrdDraftApproved(faction=rival_faction, month=3),
        FactionMonthPlanned(faction=rival_faction, month=3),
    ]


@pytest.mark.django_db
def test_handle_plan_faction_month_decides_nothing_for_the_player():
    """
    His draft is a button on his fyrd card and his hiring one in his pub - but his restock hangs off
    this too, so the closing event still comes out.
    """
    player_faction, _ = _rival_with_pub(purse=1000, salary_list=[100], fyrd_reserve=2)
    player_faction.savegame.player_faction = player_faction
    player_faction.savegame.save()

    result = handle_plan_faction_month(context=PlanFactionMonth(faction=player_faction, month=3))

    assert result == [FactionMonthPlanned(faction=player_faction, month=3)]


@pytest.mark.django_db
def test_handle_plan_faction_month_buys_for_a_rival_off_its_own_shelf():
    """
    The rival's one man is bare-handed, so a 2d6 sword (7) lifts him over the fallback's 2 - the
    purchase is weighed against the gear the snapshot read off the roster, and the approval carries
    the item off the shelf.
    """
    rival_faction = FactionFactory(fyrd_reserve=0, town__hall=Town.HallChoices.HALL_LARGE)
    WarriorFactory(faction=rival_faction, monthly_salary=50)
    TransactionFactory(faction=rival_faction, amount=1000)
    sword = ItemFactory(
        savegame=rival_faction.savegame,
        owner=None,
        price=60,
        type=ItemTypeFactory(base_value="2d6", function=ItemType.FunctionChoices.FUNCTION_WEAPON),
    )
    rival_faction.available_items.add(sword)

    result = handle_plan_faction_month(context=PlanFactionMonth(faction=rival_faction, month=3))

    assert result == [
        ShopItemPurchaseApproved(faction=rival_faction, item=sword, month=3),
        FactionMonthPlanned(faction=rival_faction, month=3),
    ]


@pytest.mark.django_db
def test_handle_plan_faction_month_raises_the_hall_of_a_rival_with_a_man_to_man_it():
    """
    The hall goes out with its level and price settled, and before the closing event - so the pub
    restock that hangs off it already counts the slots of the bigger hall.
    """
    rival_faction = FactionFactory(fyrd_reserve=0)
    WarriorFactory(faction=rival_faction, monthly_salary=150)
    TransactionFactory(faction=rival_faction, amount=1000)

    result = handle_plan_faction_month(context=PlanFactionMonth(faction=rival_faction, month=3))

    assert result == [
        TownBuildingUpgradeApproved(
            faction=rival_faction, town=rival_faction.town, building_type="hall", new_level=1, costs=600, month=3
        ),
        FactionMonthPlanned(faction=rival_faction, month=3),
    ]


@pytest.mark.django_db
def test_handle_plan_faction_month_raises_no_hall_for_a_rival_that_built_this_month():
    # The once-a-month rule is the player's own, asked through the same refusal his town page asks
    rival_faction = FactionFactory(fyrd_reserve=0)
    rival_faction.town.last_constructed_building_at = rival_faction.savegame.current_month
    rival_faction.town.save()
    WarriorFactory(faction=rival_faction, monthly_salary=150)
    TransactionFactory(faction=rival_faction, amount=1000)

    result = handle_plan_faction_month(context=PlanFactionMonth(faction=rival_faction, month=3))

    assert result == [FactionMonthPlanned(faction=rival_faction, month=3)]


@pytest.mark.django_db
def test_handle_plan_faction_month_raises_no_hall_for_a_rival_of_its_leader_alone():
    """
    The hall pays for the men on the payroll, and the leader draws no wage - so a Small Hall over a
    roster of him alone pays the 50 the town already earns, and is not worth its 600.
    """
    rival_faction = FactionFactory(fyrd_reserve=0)
    WarriorFactory(faction=rival_faction, monthly_salary=0)
    TransactionFactory(faction=rival_faction, amount=1000)

    result = handle_plan_faction_month(context=PlanFactionMonth(faction=rival_faction, month=3))

    assert result == [FactionMonthPlanned(faction=rival_faction, month=3)]
