import json
import random
from unittest import mock

import pytest
from django.urls import reverse

from apps.warband.faction.domain.fyrd_reserve import FyrdReserve
from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.finance.models import Transaction
from apps.warband.finance.tests.factories.transaction import TransactionFactory
from apps.warband.incident.incidents.burnt_village_refugees import BurntVillageRefugees
from apps.warband.incident.incidents.elf_shot_herd import ElfShotHerd
from apps.warband.incident.models.pending_incident import PendingIncident
from apps.warband.incident.tests.factories.pending_incident import PendingIncidentFactory
from apps.warband.item.models.item_type import ItemType
from apps.warband.item.tests.factories.item import ItemFactory
from apps.warband.item.tests.factories.item_type import ItemTypeFactory
from apps.warband.month.models.player_month_log import PlayerMonthLog
from apps.warband.quest.models.quest import Quest
from apps.warband.savegame.models.savegame import Savegame
from apps.warband.skirmish.models.warrior import Warrior
from apps.warband.skirmish.tests.factories.skirmish import SkirmishFactory
from apps.warband.skirmish.tests.factories.warrior import WarriorFactory
from apps.warband.town.models import Town
from apps.warband.training.models import Training
from apps.warband.training.tests.factories.training import TrainingFactory
from apps.warband.warrior.services.generators.warrior.fyrd import FyrdWarriorGenerator


@pytest.mark.django_db
def test_finish_month_view_advances_the_savegame_to_the_next_month(logged_in_client, current_savegame):
    """
    Flow test: no mocking inside the chain, so this runs the real month change and asserts the end state.

    The chain trains the warriors of the current training and restocks the bulletin board, so the
    savegame needs a training and a faction to send the player against.
    """
    TrainingFactory(faction=current_savegame.player_faction)
    FactionFactory(savegame=current_savegame)

    response = logged_in_client.post(reverse("warband:finish-month-view"), data={"month": 1})

    assert response.status_code == 200
    assert response["HX-Redirect"] == reverse("warband:dashboard-view")
    current_savegame.refresh_from_db()
    assert current_savegame.current_month == 2


@pytest.mark.django_db
def test_finish_month_view_lets_a_rival_faction_recover(logged_in_client, current_savegame):
    """
    Flow test rather than a unit test on purpose: that the rivals are announced at all only exists in
    the registry, and strict mode's database blocker applies to nothing but a real queue run.

    A warrior knocked unconscious in a battle keeps his condition and his health, and rivals used to
    get no month at all - so a faction that survived one attack stayed crippled for the rest of the
    game and could never be knocked out again. Healing lifts him above zero health, which is what
    turns the condition back to healthy, whatever the sanctuary rolls.
    """
    TrainingFactory(faction=current_savegame.player_faction)
    rival_faction = FactionFactory(savegame=current_savegame)
    rival_warrior = WarriorFactory(
        faction=rival_faction,
        savegame=current_savegame,
        condition=Warrior.ConditionChoices.CONDITION_UNCONSCIOUS,
        current_health=0,
        max_health=20,
    )

    response = logged_in_client.post(reverse("warband:finish-month-view"), data={"month": 1})

    assert response.status_code == 200
    rival_warrior.refresh_from_db()
    assert rival_warrior.condition == Warrior.ConditionChoices.CONDITION_HEALTHY


@pytest.mark.django_db
def test_finish_month_view_logs_the_recovery_of_the_player_faction_only(logged_in_client, current_savegame):
    """
    Flow test rather than a unit test: that the rivals get a month at all only exists in the
    registry, and the producers of these log lines are two handlers away from the one guarding them.

    Both warriors heal - recovery is faction-wide on purpose - but only one of them is bookkeeping
    the player has any business reading. Rival lines used to outnumber his own, a savegame starting
    with three to five of them.
    """
    TrainingFactory(faction=current_savegame.player_faction)
    WarriorFactory(faction=current_savegame.player_faction, current_health=16, max_health=20)
    rival_faction = FactionFactory(savegame=current_savegame)
    WarriorFactory(faction=rival_faction, current_health=18, max_health=20)

    response = logged_in_client.post(reverse("warband:finish-month-view"), data={"month": 1})

    assert response.status_code == 200
    assert PlayerMonthLog.objects.filter(faction=current_savegame.player_faction).exists() is True
    assert PlayerMonthLog.objects.filter(faction=rival_faction).exists() is False


@pytest.mark.django_db
def test_finish_month_view_keeps_an_unpaid_warriors_morale_down(logged_in_client, current_savegame):
    """
    Flow test rather than a unit test, because what it pins is the ordering of two commands and
    nothing but a real queue run has one.

    The morale sweep refills to the maximum, so it has to see the unpaid count the salary run wrote
    this same month - handle_prepare_month returns PlayerMonthPrepared ahead of the
    FactionMonthPrepared list and queuebie drains in order. Reverse the two and this warrior ends the
    month at 20 minus the penalty instead: replenished first, docked afterwards, no worse off for
    having gone unpaid.

    He starts below his maximum on purpose. At full morale the sweep would pass him over anyway and
    the test would hold whichever way round the two ran.
    """
    warrior = WarriorFactory(
        faction=current_savegame.player_faction, current_morale=10, max_morale=20, monthly_salary=500
    )

    response = logged_in_client.post(reverse("warband:finish-month-view"), data={"month": 1})

    assert response.status_code == 200
    warrior.refresh_from_db()
    assert (warrior.unpaid_months, warrior.current_morale) == (1, 5)


@pytest.mark.django_db
def test_finish_month_view_bills_the_wages_before_the_buildings_pay_out(logged_in_client, current_savegame):
    """
    Flow test rather than a unit test, because what it pins is when a ledger row lands and nothing
    but a real queue run has an answer.

    This warrior costs less than the hall earns, and still goes unpaid: the hall's income returns an
    event, and the "CreateTransaction" it becomes is queued behind every command the month's events
    raised, the salary run among them. So the payroll reads the purse before the income reaches it.
    That is what the cost card and the navbar promise the player - a wage bill measured against
    today's silver, with the income funding the month after - and a change that let the income land
    early would silently turn every one of those warnings into a false alarm.
    """
    warrior = WarriorFactory(faction=current_savegame.player_faction, monthly_salary=40)

    response = logged_in_client.post(reverse("warband:finish-month-view"), data={"month": 1})

    assert response.status_code == 200
    warrior.refresh_from_db()
    assert warrior.unpaid_months == 1


@pytest.mark.django_db
def test_finish_month_view_moves_a_rivals_roster_and_purse(logged_in_client, current_savegame):
    """
    The whole story in one run, and a flow test because none of it exists anywhere else: that the
    rivals get a month at all lives only in the registry, and every guard deciding which faction gets
    which half of the bookkeeping sits a command handler away from the event that raised it.

    The rival lives on its town the way the player does: the 50 a town without a hall pays, less the
    150 its man draws. It raises a Small Hall for the man it has on the payroll, through the player's
    own upgrade, and calls another man up out of its fyrd. The player's month log stays his own
    throughout, which is the regression this keeps closed: every one of those steps emits a log line,
    and a savegame carries three to five rivals whose lines would bury his.
    """
    TrainingFactory(faction=current_savegame.player_faction)
    rival_faction = FactionFactory(savegame=current_savegame, fyrd_reserve=2)
    WarriorFactory(faction=rival_faction, savegame=current_savegame, monthly_salary=150)
    TransactionFactory(faction=rival_faction, amount=1000, month=1)

    response = logged_in_client.post(reverse("warband:finish-month-view"), data={"month": 1})

    assert response.status_code == 200
    # Started on 1000, took 50 from its town, paid 150 of wages and 600 for the hall; the draft is free
    assert Transaction.objects.current_balance(faction_id=rival_faction.id) == 300
    assert Warrior.objects.filter(faction=rival_faction).count() == 2
    rival_faction.town.refresh_from_db()
    assert rival_faction.town.hall == Town.HallChoices.HALL_SMALL


@pytest.mark.django_db
def test_finish_month_view_weighs_a_rivals_draft_against_the_purse_the_month_opened_with(
    logged_in_client, current_savegame
):
    """
    Flow test rather than a unit test: a unit test is handed a balance, so it cannot tell which balance
    the handler would have seen in a real month.

    This rival opens on 100 against a wage bill of 150, so it does not draft - even though the 250 of
    income it takes this month would have covered the man twice over. Nothing the month earns reaches
    the ledger until every command the month's events raised has run, the draft decision included, so
    the purse it weighs is the one it started on. Reading the later balance instead would draft here.
    """
    TrainingFactory(faction=current_savegame.player_faction)
    rival_faction = FactionFactory(savegame=current_savegame, fyrd_reserve=2)
    WarriorFactory(faction=rival_faction, savegame=current_savegame, monthly_salary=150)
    TransactionFactory(faction=rival_faction, amount=100, month=1)

    response = logged_in_client.post(reverse("warband:finish-month-view"), data={"month": 1})

    assert response.status_code == 200
    assert Warrior.objects.filter(faction=rival_faction).count() == 1


@pytest.mark.django_db
def test_finish_month_view_trains_a_rivals_warriors(logged_in_client, current_savegame):
    """
    Flow test rather than a unit test: which event the training hangs off is the whole of this story,
    and that lives only in the registry.

    No patched randomness and none tolerated either - the outcome is pinned by the setup. Swiftness
    draws its attribute from a single-entry tuple, and the improvement is floored at 1, so a bar
    standing at 99 fills whatever the roll. Patching here would reach further than the training:
    "random.choice" is one module object, and the same month restocks a shop and a pub off it.

    The player's log stays his own throughout - every upgrade emits a line, and a war band of rivals
    improving every month would bury his.
    """
    rival_faction = FactionFactory(savegame=current_savegame)
    rival_warrior = WarriorFactory(
        faction=rival_faction, savegame=current_savegame, dexterity=10, dexterity_progress=99
    )
    TrainingFactory(faction=rival_faction, category=Training.TrainingCategory.SWIFTNESS)

    response = logged_in_client.post(reverse("warband:finish-month-view"), data={"month": 1})

    assert response.status_code == 200
    rival_warrior.refresh_from_db()
    assert (rival_warrior.dexterity, rival_warrior.dexterity_progress) == (11, 0)
    assert PlayerMonthLog.objects.filter(faction=rival_faction).exists() is False


@pytest.mark.django_db
def test_finish_month_view_keeps_a_rivals_bookkeeping_out_of_the_players_log(logged_in_client, current_savegame):
    """
    Guarded at the choke point rather than per producer: the handlers raising these lines are event
    handlers, where strict mode forbids the relation traversal the check needs.
    """
    TrainingFactory(faction=current_savegame.player_faction)
    rival_faction = FactionFactory(savegame=current_savegame, fyrd_reserve=2)
    WarriorFactory(faction=rival_faction, savegame=current_savegame, monthly_salary=150)
    TransactionFactory(faction=rival_faction, amount=1000, month=1)

    response = logged_in_client.post(reverse("warband:finish-month-view"), data={"month": 1})

    assert response.status_code == 200
    assert PlayerMonthLog.objects.filter(faction=rival_faction).exists() is False


@pytest.mark.django_db
def test_finish_month_view_refuses_a_finished_savegame(logged_in_client, current_savegame):
    """
    Covers the htmx branch of RunningSavegameRequiredMixin; which views carry it at all is asserted
    separately in apps/common/tests/test_ended_savegame_guard.py, and the full-page branch is covered
    by the quest accept view, which is one of the two navigations behind the guard.

    The header is what the browser really sends here - base.html drives this button with "hx-post" -
    and an empty 204 is only the right refusal for a request that can act on one.
    """
    current_savegame.outcome = Savegame.OutcomeChoices.OUTCOME_LOST
    current_savegame.save()

    response = logged_in_client.post(
        reverse("warband:finish-month-view"), data={"month": 1}, headers={"hx-request": "true"}
    )

    assert response.status_code == 204
    assert json.loads(response["HX-Trigger"]) == {"notification": "This game is over. Start a new savegame to play on."}
    current_savegame.refresh_from_db()
    assert current_savegame.current_month == 1


@pytest.mark.django_db
def test_finish_month_view_keeps_the_month_open_while_a_skirmish_is_unresolved(logged_in_client, current_savegame):
    SkirmishFactory(attacking_faction=current_savegame.player_faction)

    response = logged_in_client.post(reverse("warband:finish-month-view"), data={"month": 1})

    assert response.status_code == 204
    assert json.loads(response["HX-Trigger"]) == {
        "notification": "Please resolve all open skirmishes before you finish this month."
    }
    current_savegame.refresh_from_db()
    assert current_savegame.current_month == 1


@pytest.mark.django_db
def test_finish_month_view_keeps_the_month_open_while_a_rivals_skirmish_is_unresolved(
    logged_in_client, current_savegame
):
    """
    The refusal is savegame-wide, not the player's fights only: an open fight of any faction would be
    a fight from last month once the month turned.
    """
    rival_faction = FactionFactory(savegame=current_savegame)
    SkirmishFactory(attacking_faction=rival_faction, defending_faction=FactionFactory(savegame=current_savegame))

    response = logged_in_client.post(reverse("warband:finish-month-view"), data={"month": 1})

    assert "HX-Trigger" in response
    current_savegame.refresh_from_db()
    assert current_savegame.current_month == 1


@pytest.mark.django_db
def test_finish_month_view_ignores_an_open_skirmish_of_another_savegame(logged_in_client, current_savegame):
    TrainingFactory(faction=current_savegame.player_faction)
    FactionFactory(savegame=current_savegame)
    SkirmishFactory(attacking_faction=FactionFactory(), victorious_faction=None)

    response = logged_in_client.post(reverse("warband:finish-month-view"), data={"month": 1})

    assert response.status_code == 200
    current_savegame.refresh_from_db()
    assert current_savegame.current_month == 2


@pytest.mark.django_db
def test_finish_month_view_leaves_a_month_the_page_did_not_show(logged_in_client, current_savegame):
    """
    The second click of a double click lands after the first has finished month 1, still posting
    month 1. Finishing whatever month is current would run month 2 without the player having seen it.
    """
    current_savegame.current_month = 2
    current_savegame.save()

    response = logged_in_client.post(reverse("warband:finish-month-view"), data={"month": 1})

    assert response["HX-Redirect"] == reverse("warband:dashboard-view")
    current_savegame.refresh_from_db()
    assert current_savegame.current_month == 2


@pytest.mark.django_db
def test_finish_month_view_refuses_a_post_without_a_month(logged_in_client, current_savegame):
    response = logged_in_client.post(reverse("warband:finish-month-view"))

    assert response.status_code == 400
    current_savegame.refresh_from_db()
    assert current_savegame.current_month == 1


@pytest.mark.django_db
def test_finish_month_view_without_an_active_savegame(logged_in_client):
    response = logged_in_client.post(reverse("warband:finish-month-view"), data={"month": 1})

    assert response.status_code == 404


@pytest.mark.django_db
def test_finish_month_view_pins_the_new_month_s_quests_to_the_board(logged_in_client, current_savegame):
    """
    Flow test, because what it pins is an ordering inside one queue run.

    The board lists the offers of the month the savegame stands in. "handle_prepare_month" increments
    and saves the month before it raises anything, so the offers drawn on the way are dated to the new
    one. Were they dated to the month that ended, the board would stand empty all month.
    """
    TrainingFactory(faction=current_savegame.player_faction)
    WarriorFactory(faction=current_savegame.player_faction)

    response = logged_in_client.post(reverse("warband:finish-month-view"), data={"month": 1})

    assert response.status_code == 200
    assert set(Quest.objects.filter(faction=current_savegame.player_faction).values_list("month", flat=True)) == {2}


def _pub_mercenary(*, faction, monthly_salary: int = 100) -> Warrior:
    """
    Generated stock standing in this faction's pub since the month began, carrying gear nobody owns.

    Arrived this month, so he costs twice his wage and no surcharge - see [Warrior.hiring_price].
    """
    mercenary = WarriorFactory(
        faction=None,
        savegame=faction.savegame,
        culture=faction.culture,
        monthly_salary=monthly_salary,
        weapon=ItemFactory(owner=None),
        is_pub_stock=True,
        pub_arrival_month=faction.savegame.current_month,
    )
    faction.available_mercenaries.add(mercenary)

    return mercenary


@pytest.mark.django_db
def test_finish_month_view_lets_a_rival_hire_the_man_in_its_pub(logged_in_client, current_savegame):
    """
    Flow test, because the ordering is the story: the restock clears the shelf with a row delete, and
    the man a rival chose must be off it by then. Only a real queue run shows that the hire the rival
    decided on lands before its pub is swept, through the same command the player's pub dispatches -
    faction, gear, shelf and ledger all moving together.

    The rival's fyrd is empty and stays empty through the month's replenishment, because a rival with
    free men left in it hires nobody.
    """
    TrainingFactory(faction=current_savegame.player_faction)
    rival_faction = FactionFactory(savegame=current_savegame, fyrd_reserve=0)
    TransactionFactory(faction=rival_faction, amount=1000, month=1)
    mercenary = _pub_mercenary(faction=rival_faction)

    with mock.patch.object(FyrdReserve, "roll_monthly_recruits", return_value=0):
        response = logged_in_client.post(reverse("warband:finish-month-view"), data={"month": 1})

    assert response.status_code == 200
    mercenary.refresh_from_db()
    assert (
        mercenary.faction,
        mercenary.weapon.owner,
        rival_faction.available_mercenaries.filter(id=mercenary.id).exists(),
        Transaction.objects.filter(faction=rival_faction, amount=-200).exists(),
    ) == (rival_faction, rival_faction, False, True)


@pytest.mark.django_db
def test_finish_month_view_restocks_every_pub_on_its_own(logged_in_client, current_savegame):
    """
    Flow test across a month boundary with several factions: every pub restocks off its own hall, and
    the player's is exactly what it would have been without rivals - his own stock, his own count, no
    man rolled for somebody else. A rival that cannot afford its man leaves him to the sweep, and the
    rival restocks are no lines in the player's log.
    """
    TrainingFactory(faction=current_savegame.player_faction)
    player_faction = current_savegame.player_faction
    rich_rival = FactionFactory(savegame=current_savegame)
    TransactionFactory(faction=rich_rival, amount=1000, month=1)
    poor_rival = FactionFactory(savegame=current_savegame)
    unaffordable_mercenary = _pub_mercenary(faction=poor_rival)
    _pub_mercenary(faction=player_faction)

    response = logged_in_client.post(reverse("warband:finish-month-view"), data={"month": 1})

    assert response.status_code == 200
    # No hall anywhere, so one fresh mercenary in each pub, and the poor rival's man swept with the stock
    assert (
        [
            pub.available_mercenaries.filter(is_pub_stock=True, pub_arrival_month=2).count()
            for pub in (player_faction, rich_rival, poor_rival)
        ],
        player_faction.available_mercenaries.count(),
        Warrior.objects.filter(id=unaffordable_mercenary.id).exists(),
        PlayerMonthLog.objects.filter(faction__in=(rich_rival, poor_rival)).exists(),
    ) == ([1, 1, 1], 1, False, False)


@pytest.mark.django_db
def test_finish_month_view_draws_no_cost_the_wages_leave_no_room_for(logged_in_client, current_savegame):
    """
    Flow test, because the defect is two checks that each pass on their own: the incident is drawn
    against the balance the month opened with, and the salary run bills that same balance, since no
    ledger row of the month lands before it. Weighed against the raw 100, the herd's 60 and the wage
    of 100 both go through and the month ends in the red.

    The draw is steered, not replaced: "random.choices" is one module object, and the same month
    restocks a shop and a pub off it, so every other call passes through to the real function. Only
    the incident pool - the one population led by the quiet month's None - is answered, with the herd
    whenever it is a candidate. The quiet month that comes back otherwise is the precondition refusing
    it, not the dice.
    """
    TrainingFactory(faction=current_savegame.player_faction)
    FactionFactory(savegame=current_savegame)
    player_faction = current_savegame.player_faction
    WarriorFactory(faction=player_faction, monthly_salary=100)
    TransactionFactory(faction=player_faction, amount=100, month=1)
    real_choices = random.choices

    def draw_the_herd_when_possible(population, *args, **kwargs) -> list:
        if population and population[0] is None:
            return [ElfShotHerd] if ElfShotHerd in population else [None]
        return real_choices(population, *args, **kwargs)

    with mock.patch("random.choices", side_effect=draw_the_herd_when_possible):
        response = logged_in_client.post(reverse("warband:finish-month-view"), data={"month": 1})

    assert response.status_code == 200
    assert (
        Transaction.objects.filter(faction=player_faction, amount=ElfShotHerd.SILVER_CHANGE).exists(),
        Transaction.objects.current_balance(faction_id=player_faction.id) >= 0,
    ) == (False, True)


@pytest.mark.django_db
def test_finish_month_view_answers_an_open_question_by_its_default(logged_in_client, current_savegame):
    """
    Flow test, because what matters is the order the month runs in: the default's line is dated to
    the new month, so it has to survive the log clearing that runs in the same batch.
    """
    TrainingFactory(faction=current_savegame.player_faction)
    FactionFactory(savegame=current_savegame)
    PendingIncidentFactory(faction=current_savegame.player_faction, month=1)

    logged_in_client.post(reverse("warband:finish-month-view"), data={"month": 1})

    assert PendingIncident.objects.filter(month=1).exists() is False
    assert (
        PlayerMonthLog.objects.filter(
            faction=current_savegame.player_faction, month=2, title=BurntVillageRefugees.get_default_option().title
        ).exists()
        is True
    )


@pytest.mark.django_db
def test_finish_month_view_arms_a_rivals_new_levy_out_of_its_stores(logged_in_client, current_savegame):
    """
    Flow test rather than a unit test, because what it pins is two hops apart in the registry: the draft
    raises "WarriorRecruited", and the handout hanging off it has to see the man the draft just wrote.

    The rival has no men and a mail shirt in its stores, so the levy it calls up this month is the only
    one who can wear it - and he marches in it from the month he arrives rather than the one after.
    """
    TrainingFactory(faction=current_savegame.player_faction)
    rival_faction = FactionFactory(savegame=current_savegame, fyrd_reserve=1)
    # Enough to keep the levy, whom a rival only calls up once it can pay him
    TransactionFactory(faction=rival_faction, amount=100, month=1)
    mail = ItemFactory(
        savegame=current_savegame,
        owner=rival_faction,
        type=ItemTypeFactory(function=ItemType.FunctionChoices.FUNCTION_ARMOR, base_value="4d6"),
    )

    # The levy brings no armour of his own, which could roll better than the mail on the dice
    with mock.patch.object(FyrdWarriorGenerator, "chance_for_armor", 0):
        response = logged_in_client.post(reverse("warband:finish-month-view"), data={"month": 1})

    assert response.status_code == 200
    assert Warrior.objects.get(faction=rival_faction).armor == mail


@pytest.mark.django_db
def test_finish_month_view_lets_a_rival_buy_off_its_shelf_and_arm_a_man_with_it(logged_in_client, current_savegame):
    """
    Flow test, because the story is the order four hops apart land in: the purchase hands the sword over,
    the restock that follows clears the shelf while the sword is still on it, and the hand-out that
    hangs off the purchase has to find it in the stores.

    The rival's one man is bare-handed and its fyrd stays empty, so the sword is the one thing its
    month is spent on.
    """
    TrainingFactory(faction=current_savegame.player_faction)
    rival_faction = FactionFactory(savegame=current_savegame, fyrd_reserve=0)
    TransactionFactory(faction=rival_faction, amount=1000, month=1)
    warrior = WarriorFactory(faction=rival_faction, savegame=current_savegame, monthly_salary=50)
    sword = ItemFactory(
        savegame=current_savegame,
        owner=None,
        price=60,
        type=ItemTypeFactory(function=ItemType.FunctionChoices.FUNCTION_WEAPON, base_value="2d6"),
    )
    rival_faction.available_items.add(sword)

    with mock.patch.object(FyrdReserve, "roll_monthly_recruits", return_value=0):
        response = logged_in_client.post(reverse("warband:finish-month-view"), data={"month": 1})

    assert response.status_code == 200
    warrior.refresh_from_db()
    assert (
        warrior.weapon,
        rival_faction.available_items.filter(id=sword.id).exists(),
        Transaction.objects.filter(faction=rival_faction, amount=-60).exists(),
    ) == (sword, False, True)
