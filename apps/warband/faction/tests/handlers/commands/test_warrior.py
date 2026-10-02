import pytest

from apps.warband.faction.handlers.commands.warrior import (
    handle_add_warrior_to_pub,
    handle_draft_warrior_from_fyrd,
    handle_recruit_pub_mercenary,
    handle_recruit_warrior_from_quest,
    handle_restock_pub_mercenaries,
    handle_warrior_monthly_salaries,
)
from apps.warband.faction.messages.commands.warrior import (
    AddWarriorToPub,
    DraftWarriorFromFyrd,
    PayMonthlyWarriorSalaries,
    RecruitPubMercenary,
    RecruitWarriorFromQuest,
    RestockTownMercenaries,
)
from apps.warband.faction.messages.events.faction import (
    MonthlyWarriorSalariesPaid,
    MonthlyWarriorSalariesUnpaid,
)
from apps.warband.faction.messages.events.warrior import (
    PubMercenarySlotOpened,
    TownMercenariesRestocked,
    WarriorRecruited,
    WarriorWasAddedToPub,
)
from apps.warband.faction.models.faction import Faction
from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.finance.tests.factories.transaction import TransactionFactory
from apps.warband.item.models.item_type import ItemType
from apps.warband.item.tests.factories.item import ItemFactory
from apps.warband.item.tests.factories.item_type import ItemTypeFactory
from apps.warband.skirmish.models import Warrior
from apps.warband.skirmish.tests.factories.warrior import WarriorFactory
from apps.warband.town.models import Town
from apps.warband.warrior.services.generators.warrior.champion import ChampionWarriorGenerator
from apps.warband.warrior.services.generators.warrior.mercenary import MercenaryWarriorGenerator


@pytest.mark.django_db
def test_handle_restock_pub_mercenaries_requests_one_warrior_per_hall_slot():
    # A Great Hall offers two mercenary slots
    faction = FactionFactory(town__hall=Town.HallChoices.HALL_MEDIUM, is_player=True)

    result = handle_restock_pub_mercenaries(context=RestockTownMercenaries(faction=faction, month=3))

    *mercenary_slots, _ = result
    assert len(mercenary_slots) == 2
    assert result[0] == PubMercenarySlotOpened(
        savegame=faction.savegame,
        faction=None,
        pub_owner=faction,
        # Drawn per slot with order_by("?"), so everything but the culture is deterministic
        culture=result[0].culture,
        generator_class=MercenaryWarriorGenerator,
        month=3,
    )


@pytest.mark.django_db
def test_handle_restock_pub_mercenaries_announces_the_whole_pub_once():
    faction = FactionFactory(town__hall=Town.HallChoices.HALL_MEDIUM, is_player=True)

    result = handle_restock_pub_mercenaries(context=RestockTownMercenaries(faction=faction, month=3))

    assert result[-1] == TownMercenariesRestocked(faction=faction, new_mercenaries=2, month=3)


@pytest.mark.django_db
def test_handle_restock_pub_mercenaries_removes_previous_stock():
    faction = FactionFactory(is_player=True)
    faction.available_mercenaries.add(WarriorFactory(faction=faction, is_pub_stock=True))

    handle_restock_pub_mercenaries(context=RestockTownMercenaries(faction=faction, month=3))

    assert faction.available_mercenaries.count() == 0


@pytest.mark.django_db
def test_handle_restock_pub_mercenaries_leaves_a_dismissed_warrior_standing():
    """
    The clean-up is a row delete, so a man the player sent away and could take back would otherwise
    be destroyed at the start of the next month.
    """
    faction = FactionFactory(is_player=True)
    dismissed_warrior = WarriorFactory(faction=None, savegame=faction.savegame, culture=faction.culture)
    faction.available_mercenaries.add(dismissed_warrior)

    handle_restock_pub_mercenaries(context=RestockTownMercenaries(faction=faction, month=3))

    assert list(faction.available_mercenaries.all()) == [dismissed_warrior]


@pytest.mark.django_db
def test_handle_restock_pub_mercenaries_stocks_a_rivals_own_pub():
    """
    Every town has a pub, and the man rolled for a rival's stands in that rival's - named as the pub's
    owner, not as his faction, since he belongs to nobody while he waits.
    """
    rival_faction = FactionFactory()
    rival_faction.available_mercenaries.add(
        WarriorFactory(faction=None, savegame=rival_faction.savegame, culture=rival_faction.culture, is_pub_stock=True)
    )

    result = handle_restock_pub_mercenaries(context=RestockTownMercenaries(faction=rival_faction, month=3))

    assert (result[0].faction, result[0].pub_owner) == (None, rival_faction)
    assert rival_faction.available_mercenaries.count() == 0


@pytest.mark.django_db
def test_handle_add_warrior_to_pub_marks_generated_stock():
    faction = FactionFactory(is_player=True)
    mercenary = WarriorFactory(faction=None, savegame=faction.savegame, culture=faction.culture)

    result = handle_add_warrior_to_pub(
        context=AddWarriorToPub(
            savegame=faction.savegame, pub_owner=faction, warrior=mercenary, is_pub_stock=True, month=3
        )
    )

    assert result == WarriorWasAddedToPub(pub_owner=faction, warrior=mercenary, month=3)
    mercenary.refresh_from_db()
    assert mercenary.is_pub_stock is True


@pytest.mark.django_db
def test_handle_add_warrior_to_pub_stands_him_in_the_pub_named_on_the_message():
    """
    A rival's pub rather than the player's: the target is the pub owner the message carries, never the
    savegame's player faction.
    """
    player_faction = FactionFactory(is_player=True)
    rival_faction = FactionFactory(savegame=player_faction.savegame)
    mercenary = WarriorFactory(faction=None, savegame=player_faction.savegame, culture=rival_faction.culture)

    handle_add_warrior_to_pub(
        context=AddWarriorToPub(
            savegame=player_faction.savegame, pub_owner=rival_faction, warrior=mercenary, is_pub_stock=True, month=3
        )
    )

    assert (list(rival_faction.available_mercenaries.all()), player_faction.available_mercenaries.count()) == (
        [mercenary],
        0,
    )


@pytest.mark.django_db
def test_handle_add_warrior_to_pub_marks_a_dismissed_warrior_as_no_stock():
    """
    Written here rather than where the man was released, so a mercenary hired out of the pub and
    later sent away is marked afresh on the way back in instead of keeping the flag he arrived with.
    """
    faction = FactionFactory(is_player=True)
    dismissed_warrior = WarriorFactory(
        faction=None, savegame=faction.savegame, culture=faction.culture, is_pub_stock=True
    )

    handle_add_warrior_to_pub(
        context=AddWarriorToPub(
            savegame=faction.savegame, pub_owner=faction, warrior=dismissed_warrior, is_pub_stock=False, month=3
        )
    )

    dismissed_warrior.refresh_from_db()
    assert dismissed_warrior.is_pub_stock is False


@pytest.mark.django_db
def test_handle_add_warrior_to_pub_stamps_the_month_he_got_there():
    """
    All three routes onto the shelf arrive through this command, so this is the one place the wait
    [Warrior.idle_surcharge] prices can begin - and a man standing here a second time starts it
    again rather than keeping the date of the first.
    """
    faction = FactionFactory(is_player=True)
    returning_veteran = WarriorFactory(
        faction=None, savegame=faction.savegame, culture=faction.culture, pub_arrival_month=1
    )

    handle_add_warrior_to_pub(
        context=AddWarriorToPub(
            savegame=faction.savegame, pub_owner=faction, warrior=returning_veteran, is_pub_stock=False, month=9
        )
    )

    returning_veteran.refresh_from_db()
    assert returning_veteran.pub_arrival_month == 9


@pytest.mark.django_db
def test_handle_recruit_warrior_from_quest():
    """Onto the roster for nothing, drawn by the generator the quest named."""
    faction = FactionFactory()

    result = handle_recruit_warrior_from_quest(
        context=RecruitWarriorFromQuest(faction=faction, generator_class=ChampionWarriorGenerator, month=3)
    )

    warrior = Warrior.objects.get(faction=faction)
    assert result == WarriorRecruited(faction=faction, warrior=warrior, recruitment_price=0, month=3)
    assert warrior.strength_baseline == ChampionWarriorGenerator.STATS_MU


@pytest.mark.django_db
def test_handle_draft_warrior_from_fyrd_with_filled_reserve():
    faction = FactionFactory(fyrd_reserve=3)

    result = handle_draft_warrior_from_fyrd(context=DraftWarriorFromFyrd(faction=faction, month=3))

    assert result == WarriorRecruited(
        faction=faction, warrior=Warrior.objects.get(faction=faction), recruitment_price=0, month=3
    )
    faction.refresh_from_db()
    assert faction.fyrd_reserve == 2


@pytest.mark.django_db
def test_handle_draft_warrior_from_fyrd_with_empty_reserve():
    faction = FactionFactory(fyrd_reserve=0)

    result = handle_draft_warrior_from_fyrd(context=DraftWarriorFromFyrd(faction=faction, month=3))

    assert result is None
    assert Warrior.objects.filter(faction=faction).exists() is False


@pytest.mark.django_db
def test_handle_draft_warrior_from_fyrd_raises_one_man_from_the_last_in_the_reserve():
    """
    The second of two overlapping drafts: both read a reserve of 1 off the page, and the first has
    already called him up. A second warrior would be a man the reserve never held.
    """
    faction = FactionFactory(fyrd_reserve=1)
    stale_faction = Faction.objects.get(pk=faction.pk)
    handle_draft_warrior_from_fyrd(context=DraftWarriorFromFyrd(faction=faction, month=3))

    result = handle_draft_warrior_from_fyrd(context=DraftWarriorFromFyrd(faction=stale_faction, month=3))

    assert result is None
    assert Warrior.objects.filter(faction=faction).count() == 1


@pytest.mark.django_db
def test_handle_recruit_pub_mercenary_charges_nothing_for_a_man_already_hired():
    """
    The second of two overlapping hires: both found him in the pub, and the first has already taken
    him. Charging again would take his price twice for one man.
    """
    faction = FactionFactory(is_player=True)
    TransactionFactory(faction=faction, amount=1000)
    mercenary = WarriorFactory(faction=None, savegame=faction.savegame, culture=faction.culture)
    faction.available_mercenaries.add(mercenary)
    stale_mercenary = Warrior.objects.get(pk=mercenary.pk)
    handle_recruit_pub_mercenary(context=RecruitPubMercenary(warrior=mercenary, faction=faction, month=3))

    result = handle_recruit_pub_mercenary(
        context=RecruitPubMercenary(warrior=stale_mercenary, faction=faction, month=3)
    )

    assert result is None


@pytest.mark.django_db
def test_handle_recruit_pub_mercenary_leaves_him_in_the_pub_when_the_purse_no_longer_covers_him():
    """
    A hire and a purchase elsewhere, both passed by their views on the same 200 silver. The purchase
    has been paid for, so the hire has to find a purse that no longer reaches his price.
    """
    faction = FactionFactory(is_player=True)
    TransactionFactory(faction=faction, amount=200)
    TransactionFactory(faction=faction, amount=-100)
    # Priced at twice his wage, so 180 silver
    mercenary = WarriorFactory(faction=None, savegame=faction.savegame, culture=faction.culture, monthly_salary=90)
    faction.available_mercenaries.add(mercenary)

    result = handle_recruit_pub_mercenary(context=RecruitPubMercenary(warrior=mercenary, faction=faction, month=3))

    assert result is None
    assert list(faction.available_mercenaries.all()) == [mercenary]


@pytest.mark.django_db
def test_handle_recruit_pub_mercenary_takes_him_onto_the_roster():
    faction = FactionFactory(is_player=True)
    TransactionFactory(faction=faction, amount=1000)
    # Priced off the wage he draws rather than off "recruitment_price", so a veteran the player sent
    # away costs what he is worth now - see "Warrior.hiring_price"
    mercenary = WarriorFactory(faction=None, savegame=faction.savegame, culture=faction.culture, monthly_salary=90)
    faction.available_mercenaries.add(mercenary)

    result = handle_recruit_pub_mercenary(context=RecruitPubMercenary(warrior=mercenary, faction=faction, month=3))

    assert result == WarriorRecruited(warrior=mercenary, faction=faction, recruitment_price=180, month=3)
    mercenary.refresh_from_db()
    assert mercenary.faction == faction


@pytest.mark.django_db
def test_handle_recruit_pub_mercenary_bills_the_wait_he_was_left_to():
    """
    The price has to be read before the man is moved, because taking him off the shelf is what ends
    the wait it is partly made of - see [Warrior.idle_surcharge]. Read afterwards it would bill a
    veteran parked half a year as though he had never left, which is the loophole this closes.
    """
    faction = FactionFactory(savegame__current_month=7, is_player=True)
    TransactionFactory(faction=faction, amount=1000)
    veteran = WarriorFactory(
        faction=None,
        savegame=faction.savegame,
        culture=faction.culture,
        monthly_salary=90,
        pub_arrival_month=1,
    )
    faction.available_mercenaries.add(veteran)

    result = handle_recruit_pub_mercenary(context=RecruitPubMercenary(warrior=veteran, faction=faction, month=7))

    assert result == WarriorRecruited(warrior=veteran, faction=faction, recruitment_price=450, month=7)


@pytest.mark.django_db
def test_handle_recruit_pub_mercenary_ends_his_wait():
    """
    A veteran back on a roster still carrying the month he was last parked would be charged for a
    wait that ended the day the player paid for it.
    """
    faction = FactionFactory(savegame__current_month=7, is_player=True)
    TransactionFactory(faction=faction, amount=1000)
    veteran = WarriorFactory(faction=None, savegame=faction.savegame, culture=faction.culture, pub_arrival_month=1)
    faction.available_mercenaries.add(veteran)

    handle_recruit_pub_mercenary(context=RecruitPubMercenary(warrior=veteran, faction=faction, month=7))

    veteran.refresh_from_db()
    assert veteran.pub_arrival_month is None


@pytest.mark.django_db
def test_handle_recruit_pub_mercenary_takes_him_out_of_the_pub():
    """
    The monthly restock deletes what it finds in the pub, rows and all, so a hired man left linked to
    it is deleted at the start of the next month - after he has been paid for.
    """
    faction = FactionFactory(is_player=True)
    TransactionFactory(faction=faction, amount=1000)
    mercenary = WarriorFactory(faction=None, savegame=faction.savegame, culture=faction.culture)
    faction.available_mercenaries.add(mercenary)

    handle_recruit_pub_mercenary(context=RecruitPubMercenary(warrior=mercenary, faction=faction, month=3))

    assert list(faction.available_mercenaries.all()) == []


@pytest.mark.django_db
def test_handle_recruit_pub_mercenary_hands_his_gear_to_the_faction():
    """
    Pub gear is generated unowned, and unowned gear never reaches "get_all_unoccupied_items" - it
    could be neither re-equipped onto anybody else nor sold.
    """
    faction = FactionFactory(is_player=True)
    TransactionFactory(faction=faction, amount=1000)
    weapon = ItemFactory(
        type=ItemTypeFactory(function=ItemType.FunctionChoices.FUNCTION_WEAPON),
        savegame=faction.savegame,
        owner=None,
    )
    armor = ItemFactory(
        type=ItemTypeFactory(function=ItemType.FunctionChoices.FUNCTION_ARMOR),
        savegame=faction.savegame,
        owner=None,
    )
    mercenary = WarriorFactory(
        faction=None, savegame=faction.savegame, culture=faction.culture, weapon=weapon, armor=armor
    )
    faction.available_mercenaries.add(mercenary)

    handle_recruit_pub_mercenary(context=RecruitPubMercenary(warrior=mercenary, faction=faction, month=3))

    weapon.refresh_from_db()
    armor.refresh_from_db()
    assert (weapon.owner, armor.owner) == (faction, faction)


@pytest.mark.django_db
def test_handle_recruit_pub_mercenary_clears_what_he_was_owed():
    """
    The shelf holds the man who walked out over the full term of unpaid wages. Carried over, his
    count would put him one failed payroll from walking again the month after he was paid for, and
    the wage-bill warning would read "4 of 3 unpaid months" meanwhile.
    """
    faction = FactionFactory(is_player=True)
    TransactionFactory(faction=faction, amount=1000)
    mercenary = WarriorFactory(
        faction=None,
        savegame=faction.savegame,
        culture=faction.culture,
        unpaid_months=Warrior.UNPAID_MONTHS_UNTIL_WALKOUT,
    )
    faction.available_mercenaries.add(mercenary)

    handle_recruit_pub_mercenary(context=RecruitPubMercenary(warrior=mercenary, faction=faction, month=3))

    mercenary.refresh_from_db()
    assert mercenary.unpaid_months == 0


@pytest.mark.django_db
def test_handle_recruit_pub_mercenary_who_carries_nothing():
    """
    A mercenary rolls his weapon at 75% and his armor at 25%, so an empty-handed one is the common
    case rather than the edge.
    """
    faction = FactionFactory(is_player=True)
    TransactionFactory(faction=faction, amount=1000)
    mercenary = WarriorFactory(
        faction=None, savegame=faction.savegame, culture=faction.culture, weapon=None, armor=None
    )
    faction.available_mercenaries.add(mercenary)

    result = handle_recruit_pub_mercenary(context=RecruitPubMercenary(warrior=mercenary, faction=faction, month=3))

    assert result == WarriorRecruited(warrior=mercenary, faction=faction, recruitment_price=0, month=3)
    mercenary.refresh_from_db()
    assert (mercenary.weapon, mercenary.armor) == (None, None)


@pytest.mark.django_db
def test_handle_warrior_monthly_salaries_pays_a_roster_the_purse_covers():
    faction = FactionFactory()
    TransactionFactory(faction=faction, amount=1000)
    warrior = WarriorFactory(faction=faction, monthly_salary=200, unpaid_months=2)

    result = handle_warrior_monthly_salaries(context=PayMonthlyWarriorSalaries(faction=faction, month=3))

    assert result == [MonthlyWarriorSalariesPaid(faction=faction, amount=200, month=3)]
    warrior.refresh_from_db()
    assert warrior.unpaid_months == 0


@pytest.mark.django_db
def test_handle_warrior_monthly_salaries_pays_the_cheapest_warriors_first():
    """
    Paying from the cheapest up fits the most men into whatever silver there is, so the shortfall
    lands on the veterans - the ones whose salary grew with every level.
    """
    faction = FactionFactory()
    TransactionFactory(faction=faction, amount=350)
    levy = WarriorFactory(faction=faction, monthly_salary=50)
    thegn = WarriorFactory(faction=faction, monthly_salary=200)
    ealdorman = WarriorFactory(faction=faction, monthly_salary=300)

    result = handle_warrior_monthly_salaries(context=PayMonthlyWarriorSalaries(faction=faction, month=3))

    assert result == [
        MonthlyWarriorSalariesPaid(faction=faction, amount=250, month=3),
        MonthlyWarriorSalariesUnpaid(faction=faction, warrior_list=[ealdorman], missing_amount=300, month=3),
    ]
    levy.refresh_from_db()
    thegn.refresh_from_db()
    assert (levy.unpaid_months, thegn.unpaid_months, result[1].warrior_list[0].unpaid_months) == (0, 0, 1)


@pytest.mark.django_db
def test_handle_warrior_monthly_salaries_stays_silent_about_the_nothing_it_paid():
    """
    An empty purse used to still announce "salaries of 0 silver paid", writing a zero transaction and
    a log line that contradicts the shortfall printed directly under it.
    """
    faction = FactionFactory()
    warrior = WarriorFactory(faction=faction, monthly_salary=50)

    result = handle_warrior_monthly_salaries(context=PayMonthlyWarriorSalaries(faction=faction, month=3))

    assert result == [MonthlyWarriorSalariesUnpaid(faction=faction, warrior_list=[warrior], missing_amount=50, month=3)]
    warrior.refresh_from_db()
    assert warrior.unpaid_months == 1


@pytest.mark.django_db
def test_handle_warrior_monthly_salaries_pays_a_leader_on_no_wage_out_of_a_purse_in_the_red():
    """
    A shortfall of nothing is no shortfall: the leader costs no silver, so a balance below zero owes
    him nothing, reports nothing and forgives the months he is recorded as having gone without.
    """
    faction = FactionFactory()
    TransactionFactory(faction=faction, amount=-10)
    leader = WarriorFactory(faction=faction, monthly_salary=0, unpaid_months=1)

    result = handle_warrior_monthly_salaries(context=PayMonthlyWarriorSalaries(faction=faction, month=3))

    assert result == []
    leader.refresh_from_db()
    assert leader.unpaid_months == 0


@pytest.mark.django_db
def test_handle_warrior_monthly_salaries_with_an_empty_roster():
    faction = FactionFactory()

    result = handle_warrior_monthly_salaries(context=PayMonthlyWarriorSalaries(faction=faction, month=3))

    assert result == []
