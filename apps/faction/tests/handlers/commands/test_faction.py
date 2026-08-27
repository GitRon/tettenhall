from unittest import mock

import pytest

from apps.faction.handlers.commands.faction import (
    handle_create_factions_for_new_savegame,
    handle_create_new_faction,
    handle_defeat_faction_of_lost_leader,
    handle_determine_injured_warriors,
    handle_determine_warriors_with_reduced_morale,
    handle_earn_money_from_buildings,
    handle_earn_monthly_faction_income,
    handle_remove_quest_from_bulletin_board,
    handle_replenish_fyrd_reserve,
    handle_restock_shop_items,
)
from apps.faction.messages.commands.faction import (
    CreateFactionsForNewSavegame,
    CreateNewFaction,
    DefeatFactionOfLostLeader,
    DetermineInjuredWarriors,
    DetermineWarriorsWithReducedMorale,
    EarnMoneyFromBuildings,
    EarnMonthlyFactionIncome,
    RemoveQuestFromBulletinBoard,
    ReplenishFyrdReserve,
    RestockTownShopItems,
)
from apps.faction.messages.events.faction import (
    FactionFyrdReserveReplenished,
    FactionWarriorsWithReducedMoraleDetermined,
    FactionWasDefeated,
    MonthlyBuildingMoneyEarned,
    MonthlyFactionIncomeEarned,
    NewFactionCreated,
    QuestWasRemovedFromBulletinBoard,
    RequestNewItemForTownShop,
)
from apps.faction.models.culture import Culture
from apps.faction.models.faction import Faction
from apps.faction.tests.factories.culture import CultureFactory
from apps.faction.tests.factories.faction import FactionFactory
from apps.item.models import ItemType
from apps.item.services.generators.item.mercenary import MercenaryItemGenerator
from apps.item.tests.factories.item import ItemFactory
from apps.quest.tests.factories.quest import QuestFactory
from apps.savegame.tests.factories.savegame import SavegameFactory
from apps.skirmish.models.warrior import Warrior
from apps.skirmish.tests.factories.warrior import WarriorFactory
from apps.warrior.messages.commands.warrior import HealInjuredWarrior


@pytest.mark.django_db
def test_handle_create_new_faction_for_player_faction():
    savegame = SavegameFactory(current_month=5)
    culture = CultureFactory()

    with mock.patch("apps.faction.handlers.commands.faction.random.randint", return_value=4):
        result = handle_create_new_faction(
            context=CreateNewFaction(
                name="Wessex",
                town_name="Winchester",
                culture_id=culture.id,
                savegame=savegame,
                is_player_faction=True,
            )
        )

    assert result == NewFactionCreated(faction=Faction.objects.get(name="Wessex"), current_month=5)
    savegame.refresh_from_db()
    assert savegame.player_faction == result.faction
    assert result.faction.town_name == "Winchester"


@pytest.mark.django_db
def test_handle_create_new_faction_for_defending_faction():
    savegame = SavegameFactory(current_month=5)
    culture = CultureFactory()

    with mock.patch("apps.faction.handlers.commands.faction.random.randint", return_value=4):
        result = handle_create_new_faction(
            context=CreateNewFaction(
                name="Mercia",
                town_name="Tamworth",
                culture_id=culture.id,
                savegame=savegame,
                is_player_faction=False,
            )
        )

    assert result.faction.fyrd_reserve == 4
    savegame.refresh_from_db()
    assert savegame.player_faction is None


@pytest.mark.django_db
def test_handle_defeat_faction_of_lost_leader_knocks_the_faction_out():
    faction = FactionFactory()
    leader = WarriorFactory(faction=faction, savegame=faction.savegame)
    faction.leader = leader
    faction.save()

    result = handle_defeat_faction_of_lost_leader(context=DefeatFactionOfLostLeader(warrior=leader))

    assert result == FactionWasDefeated(faction=faction, savegame=faction.savegame)
    faction.refresh_from_db()
    assert faction.is_defeated is True


@pytest.mark.django_db
def test_handle_defeat_faction_of_lost_leader_for_a_captured_leader():
    """
    Capture clears the warrior's own faction before this runs, so the lookup has to go through
    Faction.leader - the only remaining record of who led whom.
    """
    faction = FactionFactory()
    leader = WarriorFactory(faction=faction, savegame=faction.savegame)
    faction.leader = leader
    faction.save()
    leader.faction = None
    leader.save()

    result = handle_defeat_faction_of_lost_leader(context=DefeatFactionOfLostLeader(warrior=leader))

    assert result == FactionWasDefeated(faction=faction, savegame=faction.savegame)


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
def test_handle_restock_shop_items_requests_weapons():
    # A Marketplace holds four stalls
    faction = FactionFactory(town__marketplace=1)

    with mock.patch("apps.faction.handlers.commands.faction.random.getrandbits", return_value=1):
        result = handle_restock_shop_items(context=RestockTownShopItems(faction=faction, month=3))

    expected_message = RequestNewItemForTownShop(
        faction=faction,
        generator_class=MercenaryItemGenerator,
        item_function=ItemType.FunctionChoices.FUNCTION_WEAPON,
        month=3,
        quality_bonus=0,
    )
    assert result == [expected_message] * 4


@pytest.mark.django_db
def test_handle_restock_shop_items_requests_armor():
    faction = FactionFactory(town__marketplace=1)

    with mock.patch("apps.faction.handlers.commands.faction.random.getrandbits", return_value=0):
        result = handle_restock_shop_items(context=RestockTownShopItems(faction=faction, month=3))

    expected_message = RequestNewItemForTownShop(
        faction=faction,
        generator_class=MercenaryItemGenerator,
        item_function=ItemType.FunctionChoices.FUNCTION_ARMOR,
        month=3,
        quality_bonus=0,
    )
    assert result == [expected_message] * 4


@pytest.mark.django_db
def test_handle_restock_shop_items_stocks_as_many_items_as_the_market_has_stalls():
    """
    The stock size used to be a dice roll between four and five, so no building had a say in it.
    """
    faction = FactionFactory(town__marketplace=3)

    result = handle_restock_shop_items(context=RestockTownShopItems(faction=faction, month=3))

    # A High Market holds eight, against the three a town without a market manages
    assert len(result) == 8


@pytest.mark.django_db
def test_handle_restock_shop_items_passes_the_quality_of_the_weaponsmith():
    faction = FactionFactory(town__weaponsmith=3)

    result = handle_restock_shop_items(context=RestockTownShopItems(faction=faction, month=3))

    # A Master Forge adds three to every modifier roll in the shop
    assert {message.quality_bonus for message in result} == {3}


@pytest.mark.django_db
def test_handle_restock_shop_items_removes_previous_stock():
    faction = FactionFactory()
    faction.available_items.add(ItemFactory())

    with (
        mock.patch("apps.faction.handlers.commands.faction.random.randrange", return_value=4),
        mock.patch("apps.faction.handlers.commands.faction.random.getrandbits", return_value=1),
    ):
        handle_restock_shop_items(context=RestockTownShopItems(faction=faction, month=3))

    assert faction.available_items.count() == 0


@pytest.mark.django_db
def test_handle_remove_quest_from_bulletin_board_takes_the_quest_off_the_board():
    faction = FactionFactory()
    quest = QuestFactory(target_faction=FactionFactory(savegame=faction.savegame))
    faction.available_quests.add(quest)

    result = handle_remove_quest_from_bulletin_board(
        context=RemoveQuestFromBulletinBoard(faction=faction, quest=quest, month=3)
    )

    assert result == QuestWasRemovedFromBulletinBoard(faction=faction, quest=quest, month=3)
    assert list(faction.available_quests.all()) == []


@pytest.mark.django_db
def test_handle_replenish_fyrd_reserve_with_new_recruitees():
    faction = FactionFactory(fyrd_reserve=3)

    with mock.patch("apps.faction.handlers.commands.faction.random.randrange", return_value=2):
        result = handle_replenish_fyrd_reserve(context=ReplenishFyrdReserve(faction=faction, month=3))

    assert result == FactionFyrdReserveReplenished(faction=faction, new_recruitees=2, month=3)
    faction.refresh_from_db()
    assert faction.fyrd_reserve == 5


@pytest.mark.django_db
def test_handle_replenish_fyrd_reserve_without_new_recruitees():
    faction = FactionFactory(fyrd_reserve=3)

    with mock.patch("apps.faction.handlers.commands.faction.random.randrange", return_value=0):
        result = handle_replenish_fyrd_reserve(context=ReplenishFyrdReserve(faction=faction, month=3))

    assert result is None
    faction.refresh_from_db()
    assert faction.fyrd_reserve == 3


@pytest.mark.django_db
def test_handle_determine_injured_warriors_with_injured_warrior():
    injured_warrior = WarriorFactory(current_health=5, max_health=20)

    result = handle_determine_injured_warriors(
        context=DetermineInjuredWarriors(faction=injured_warrior.faction, month=3)
    )

    assert result == [HealInjuredWarrior(faction=injured_warrior.faction, warrior=injured_warrior, month=3)]


@pytest.mark.django_db
def test_handle_determine_injured_warriors_without_injured_warriors():
    healthy_warrior = WarriorFactory(current_health=20, max_health=20)

    result = handle_determine_injured_warriors(
        context=DetermineInjuredWarriors(faction=healthy_warrior.faction, month=3)
    )

    assert result == []


@pytest.mark.django_db
def test_handle_determine_injured_warriors_ignores_dead_warriors():
    dead_warrior = WarriorFactory(current_health=0, max_health=20, condition=Warrior.ConditionChoices.CONDITION_DEAD)

    result = handle_determine_injured_warriors(context=DetermineInjuredWarriors(faction=dead_warrior.faction, month=3))

    assert result == []


@pytest.mark.django_db
def test_handle_determine_injured_warriors_selects_a_captive_of_this_faction():
    """
    A captive is on nobody's roster, so his captor's sweep is the only one that can reach him.
    """
    captor = FactionFactory()
    captive = WarriorFactory(
        faction=None,
        savegame=captor.savegame,
        culture=captor.culture,
        current_health=0,
        max_health=20,
        condition=Warrior.ConditionChoices.CONDITION_UNCONSCIOUS,
    )
    captor.captured_warriors.add(captive)

    result = handle_determine_injured_warriors(context=DetermineInjuredWarriors(faction=captor, month=3))

    # The captor rides along, because the mending is done at his sanctuary and logged in his month
    assert result == [HealInjuredWarrior(faction=captor, warrior=captive, month=3)]


@pytest.mark.django_db
def test_handle_determine_injured_warriors_leaves_another_factions_captive_alone():
    captor = FactionFactory()
    captive = WarriorFactory(
        faction=None,
        savegame=captor.savegame,
        culture=captor.culture,
        current_health=0,
        max_health=20,
        condition=Warrior.ConditionChoices.CONDITION_UNCONSCIOUS,
    )
    captor.captured_warriors.add(captive)
    bystander_faction = FactionFactory(savegame=captor.savegame)

    result = handle_determine_injured_warriors(context=DetermineInjuredWarriors(faction=bystander_faction, month=3))

    assert result == []


@pytest.mark.django_db
def test_handle_determine_injured_warriors_skips_a_captive_at_full_health():
    captor = FactionFactory()
    healed_captive = WarriorFactory(
        faction=None, savegame=captor.savegame, culture=captor.culture, current_health=20, max_health=20
    )
    captor.captured_warriors.add(healed_captive)

    result = handle_determine_injured_warriors(context=DetermineInjuredWarriors(faction=captor, month=3))

    assert result == []


@pytest.mark.django_db
def test_handle_determine_injured_warriors_skips_a_dead_captive():
    """
    Only the unconscious are ever taken prisoner, but a captive can be killed off the field by
    anything that reaches him, and no sanctuary mends a corpse.
    """
    captor = FactionFactory()
    dead_captive = WarriorFactory(
        faction=None,
        savegame=captor.savegame,
        culture=captor.culture,
        current_health=0,
        max_health=20,
        condition=Warrior.ConditionChoices.CONDITION_DEAD,
    )
    captor.captured_warriors.add(dead_captive)

    result = handle_determine_injured_warriors(context=DetermineInjuredWarriors(faction=captor, month=3))

    assert result == []


@pytest.mark.django_db
def test_handle_determine_warriors_with_reduced_morale_skips_warriors_at_full_morale():
    faction = FactionFactory()
    warrior_with_reduced_morale = WarriorFactory(faction=faction, current_morale=5, max_morale=20)
    WarriorFactory(faction=faction, current_morale=20, max_morale=20)

    result = handle_determine_warriors_with_reduced_morale(
        context=DetermineWarriorsWithReducedMorale(faction=faction, month=3)
    )

    assert result == FactionWarriorsWithReducedMoraleDetermined(
        faction=faction, warrior_list=[warrior_with_reduced_morale], month=3
    )


@pytest.mark.django_db
def test_handle_determine_warriors_with_reduced_morale_skips_an_unpaid_warrior():
    """
    A man who was not paid does not cheer up either. Without this the sweep would hand back every
    point insolvency had just taken, in the same month it took them, because the replenish handler
    at the end of the chain refills to the maximum.
    """
    faction = FactionFactory()
    paid_warrior = WarriorFactory(faction=faction, current_morale=5, max_morale=20)
    WarriorFactory(faction=faction, current_morale=5, max_morale=20, unpaid_months=1)

    result = handle_determine_warriors_with_reduced_morale(
        context=DetermineWarriorsWithReducedMorale(faction=faction, month=3)
    )

    assert result == FactionWarriorsWithReducedMoraleDetermined(faction=faction, warrior_list=[paid_warrior], month=3)


@pytest.mark.django_db
def test_handle_determine_warriors_with_reduced_morale_skips_dead_warriors():
    faction = FactionFactory()
    WarriorFactory(
        faction=faction,
        current_morale=5,
        max_morale=20,
        condition=Warrior.ConditionChoices.CONDITION_DEAD,
    )

    result = handle_determine_warriors_with_reduced_morale(
        context=DetermineWarriorsWithReducedMorale(faction=faction, month=3)
    )

    assert result == FactionWarriorsWithReducedMoraleDetermined(faction=faction, warrior_list=[], month=3)


@pytest.mark.django_db
def test_handle_determine_warriors_with_reduced_morale_passes_over_captives():
    """
    Health is what a captor mends, spirit is not - unlike the healing sweep, this one stays on the
    roster on purpose. Morale is refilled to the maximum further down the chain, and a month in an
    enemy cell restoring a man completely reads wrong.
    """
    captor = FactionFactory()
    captive = WarriorFactory(
        faction=None, savegame=captor.savegame, culture=captor.culture, current_morale=5, max_morale=20
    )
    captor.captured_warriors.add(captive)

    result = handle_determine_warriors_with_reduced_morale(
        context=DetermineWarriorsWithReducedMorale(faction=captor, month=3)
    )

    assert result == FactionWarriorsWithReducedMoraleDetermined(faction=captor, warrior_list=[], month=3)


@pytest.mark.django_db
def test_handle_determine_warriors_with_reduced_morale_picks_up_a_fleeing_warrior():
    """
    The half of the rally this sweep owns. Restoring the condition further down the chain only ever
    helps if the man who routed is in this list at all, and a warrior who fled without a scratch is
    in no other one - the healing sweep wants the wounded, and he is not.
    """
    faction = FactionFactory()
    fleeing_warrior = WarriorFactory(
        faction=faction,
        current_morale=0,
        max_morale=20,
        condition=Warrior.ConditionChoices.CONDITION_FLEEING,
    )

    result = handle_determine_warriors_with_reduced_morale(
        context=DetermineWarriorsWithReducedMorale(faction=faction, month=3)
    )

    assert result == FactionWarriorsWithReducedMoraleDetermined(
        faction=faction, warrior_list=[fleeing_warrior], month=3
    )


@pytest.mark.django_db
def test_handle_create_factions_for_new_savegame_starts_with_the_player_faction():
    savegame = SavegameFactory()
    culture = CultureFactory()

    with mock.patch("apps.faction.handlers.commands.faction.random.randint", return_value=3):
        result = handle_create_factions_for_new_savegame(
            context=CreateFactionsForNewSavegame(
                savegame=savegame, faction_name="Wessex", town_name="Winchester", faction_culture_id=culture.id
            )
        )

    assert result[0] == CreateNewFaction(
        name="Wessex", town_name="Winchester", savegame=savegame, culture_id=culture.id, is_player_faction=True
    )


@pytest.mark.django_db
def test_handle_create_factions_for_new_savegame_adds_the_drawn_number_of_rival_factions():
    savegame = SavegameFactory()
    culture = CultureFactory()

    with mock.patch("apps.faction.handlers.commands.faction.random.randint", return_value=3):
        result = handle_create_factions_for_new_savegame(
            context=CreateFactionsForNewSavegame(
                savegame=savegame, faction_name="Wessex", town_name="Winchester", faction_culture_id=culture.id
            )
        )

    assert len(result) == 4
    assert result[3].is_player_faction is False
    # Rival factions get a generated town of their own instead of the player's
    assert result[3].town_name != ""
    assert result[3].town_name != "Winchester"


@pytest.mark.django_db
def test_handle_create_factions_for_new_savegame_without_the_culture():
    """
    Cultures are reference data every environment ships with, so a missing one is a half-seeded
    database rather than bad input - and it used to surface one line later as "NoneType has no
    attribute locale".

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
    # A Great Hall brings in 550 silver a month
    faction = FactionFactory(town__hall=2)

    result = handle_earn_money_from_buildings(context=EarnMoneyFromBuildings(faction=faction, month=3))

    assert result == MonthlyBuildingMoneyEarned(faction=faction, amount=550, month=3)


@pytest.mark.django_db
def test_handle_earn_money_from_buildings_without_a_hall():
    faction = FactionFactory()

    result = handle_earn_money_from_buildings(context=EarnMoneyFromBuildings(faction=faction, month=3))

    # A town without a hall still trickles in a baseline
    assert result == MonthlyBuildingMoneyEarned(faction=faction, amount=50, month=3)


@pytest.mark.django_db
def test_handle_earn_monthly_faction_income_scales_with_the_healthy_roster():
    player_faction = FactionFactory()
    player_faction.savegame.player_faction = player_faction
    player_faction.savegame.save()
    rival_faction = FactionFactory(savegame=player_faction.savegame)
    WarriorFactory(faction=rival_faction)
    WarriorFactory(faction=rival_faction)

    result = handle_earn_monthly_faction_income(context=EarnMonthlyFactionIncome(faction=rival_faction, month=3))

    # 50 of baseline plus 200 for each of the two men it can field
    assert result == MonthlyFactionIncomeEarned(faction=rival_faction, amount=450, month=3)


@pytest.mark.django_db
def test_handle_earn_monthly_faction_income_leaves_out_the_warriors_who_are_down():
    """
    A faction that cannot field a warrior should not be earning off him - while the wage bill covers
    him all the same, which is the squeeze a beaten faction is under.
    """
    player_faction = FactionFactory()
    player_faction.savegame.player_faction = player_faction
    player_faction.savegame.save()
    rival_faction = FactionFactory(savegame=player_faction.savegame)
    WarriorFactory(faction=rival_faction)
    WarriorFactory(faction=rival_faction, condition=Warrior.ConditionChoices.CONDITION_UNCONSCIOUS)

    result = handle_earn_monthly_faction_income(context=EarnMonthlyFactionIncome(faction=rival_faction, month=3))

    assert result.amount == 250


@pytest.mark.django_db
def test_handle_earn_monthly_faction_income_refuses_the_player():
    """
    The player has the buildings, so taking this as well would pay him twice for the same month.
    """
    player_faction = FactionFactory()
    player_faction.savegame.player_faction = player_faction
    player_faction.savegame.save()

    result = handle_earn_monthly_faction_income(context=EarnMonthlyFactionIncome(faction=player_faction, month=3))

    assert result is None
