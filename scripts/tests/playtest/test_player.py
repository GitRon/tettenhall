import pytest

from apps.warband.faction.models.faction import Faction
from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.finance.tests.factories.transaction import TransactionFactory
from apps.warband.item.models.item import Item
from apps.warband.item.models.item_type import ItemType
from apps.warband.item.tests.factories.item import ItemFactory
from apps.warband.item.tests.factories.item_type import ItemTypeFactory
from apps.warband.quest.models.quest_contract import QuestContract
from apps.warband.quest.quests.drive_off_wolves import DriveOffWolves
from apps.warband.quest.quests.harvest_hands import HarvestHands
from apps.warband.quest.tests.factories.quest import QuestFactory
from apps.warband.savegame.models.savegame import Savegame
from apps.warband.skirmish.choices.raid_kind import RaidKindChoices
from apps.warband.skirmish.models.skirmish import Skirmish
from apps.warband.skirmish.models.warrior import Warrior
from apps.warband.skirmish.tests.factories.skirmish import SkirmishFactory
from apps.warband.skirmish.tests.factories.warrior import WarriorFactory
from apps.warband.town.buildings.hall import Hall
from scripts.playtest.player import STOP_FIGHT_STUCK, PlayerTurn
from scripts.playtest.policy import POLICIES


@pytest.mark.django_db
def test_play_rides_into_a_town_nobody_holds(player_savegame, rng, report, queuebie_registry):
    """
    Occupying is a step of every month, not only of a month with a fight: the rival's one man is down
    before the month starts, so there is nobody to march on and still a town to take.
    """
    rival = FactionFactory(savegame=player_savegame)
    rival.leader = WarriorFactory(faction=rival, condition=Warrior.ConditionChoices.CONDITION_UNCONSCIOUS)
    rival.save()

    PlayerTurn(savegame=player_savegame, policy=POLICIES["aggressive"], rng=rng, report=report).play()

    rival.refresh_from_db()
    assert rival.is_defeated is True
    assert report.occupations == 1


@pytest.mark.django_db
def test_play_stops_on_a_fight_it_cannot_finish(player_savegame, rng, report, queuebie_registry):
    """
    The month goes no further than a fight that never came to a victor - not even to the occupation. A
    second rival's town stands empty, so a turn that carried on would ride into it.
    """
    rival = FactionFactory(savegame=player_savegame)
    rival.leader = WarriorFactory(faction=rival)
    rival.save()
    empty_town_rival = FactionFactory(savegame=player_savegame)
    empty_town_rival.leader = WarriorFactory(
        faction=empty_town_rival, condition=Warrior.ConditionChoices.CONDITION_UNCONSCIOUS
    )
    empty_town_rival.save()

    result = PlayerTurn(
        savegame=player_savegame, policy=POLICIES["aggressive"], rng=rng, report=report, max_rounds=0
    ).play()

    assert result == STOP_FIGHT_STUCK
    assert report.occupations == 0


@pytest.mark.django_db
def test_take_in_captives_recruits_every_prisoner(player_savegame, rng, report, queuebie_registry):
    faction = player_savegame.player_faction
    captive = WarriorFactory(faction=None, savegame=player_savegame, culture=faction.culture)
    faction.captured_warriors.add(captive)

    PlayerTurn(savegame=player_savegame, policy=POLICIES["aggressive"], rng=rng, report=report).take_in_captives()

    captive.refresh_from_db()
    assert captive.faction == faction
    assert report.captives_recruited == 1


@pytest.mark.django_db
def test_draft_the_fyrd_raises_the_whole_reserve(player_savegame, rng, report, queuebie_registry):
    faction = player_savegame.player_faction
    faction.fyrd_reserve = 2
    faction.save()

    PlayerTurn(savegame=player_savegame, policy=POLICIES["aggressive"], rng=rng, report=report).draft_the_fyrd()

    faction.refresh_from_db()
    assert faction.fyrd_reserve == 0
    assert report.drafted == 2


@pytest.mark.django_db
def test_hire_from_the_pub_hires_while_the_silver_lasts(player_savegame, rng, report, queuebie_registry):
    faction = player_savegame.player_faction
    mercenary = WarriorFactory(faction=None, savegame=player_savegame, culture=faction.culture)
    faction.available_mercenaries.add(mercenary)
    TransactionFactory(faction=faction, amount=mercenary.hiring_price + 150)

    PlayerTurn(savegame=player_savegame, policy=POLICIES["aggressive"], rng=rng, report=report).hire_from_the_pub()

    mercenary.refresh_from_db()
    assert mercenary.faction == faction
    assert report.hired == 1


@pytest.mark.django_db
def test_hire_from_the_pub_keeps_silver_back(player_savegame, rng, report, queuebie_registry):
    """He could pay for the man, but not and still keep the 150 that carry the wage bill."""
    faction = player_savegame.player_faction
    mercenary = WarriorFactory(faction=None, savegame=player_savegame, culture=faction.culture)
    faction.available_mercenaries.add(mercenary)
    TransactionFactory(faction=faction, amount=mercenary.hiring_price + 149)

    PlayerTurn(savegame=player_savegame, policy=POLICIES["aggressive"], rng=rng, report=report).hire_from_the_pub()

    mercenary.refresh_from_db()
    assert mercenary.faction is None
    assert report.hired == 0


def _sword(*, savegame: Savegame, owner: Faction | None = None, base_value: str = "2d6") -> Item:
    return ItemFactory(
        savegame=savegame,
        owner=owner,
        price=60,
        type=ItemTypeFactory(function=ItemType.FunctionChoices.FUNCTION_WEAPON, base_value=base_value),
    )


@pytest.mark.django_db
def test_buy_from_the_shop_buys_what_lifts_the_weakest_man(player_savegame, rng, report, queuebie_registry):
    """The leader is bare-handed, so a 2d6 sword (7) lifts him over the fallback's 2."""
    faction = player_savegame.player_faction
    sword = _sword(savegame=player_savegame)
    faction.available_items.add(sword)
    TransactionFactory(faction=faction, amount=60 + 150)

    PlayerTurn(savegame=player_savegame, policy=POLICIES["aggressive"], rng=rng, report=report).buy_from_the_shop()

    sword.refresh_from_db()
    assert sword.owner == faction
    assert report.items_bought == 1


@pytest.mark.django_db
def test_buy_from_the_shop_keeps_silver_back(player_savegame, rng, report, queuebie_registry):
    """He could pay for the sword, but not and still keep the 150 that carry the wage bill."""
    faction = player_savegame.player_faction
    sword = _sword(savegame=player_savegame)
    faction.available_items.add(sword)
    TransactionFactory(faction=faction, amount=60 + 149)

    PlayerTurn(savegame=player_savegame, policy=POLICIES["aggressive"], rng=rng, report=report).buy_from_the_shop()

    sword.refresh_from_db()
    assert sword.owner is None
    assert report.items_bought == 0


@pytest.mark.django_db
def test_buy_from_the_shop_buys_nothing_that_lifts_nobody(player_savegame, rng, report, queuebie_registry):
    """A 1d2 club (1.5) is worse than the bare hands the leader already fights with (2)."""
    faction = player_savegame.player_faction
    club = _sword(savegame=player_savegame, base_value="1d2")
    faction.available_items.add(club)
    TransactionFactory(faction=faction, amount=10_000)

    PlayerTurn(savegame=player_savegame, policy=POLICIES["aggressive"], rng=rng, report=report).buy_from_the_shop()

    club.refresh_from_db()
    assert club.owner is None
    assert report.items_bought == 0


@pytest.mark.django_db
def test_hand_out_gear_puts_a_stored_item_on_the_man_it_lifts(player_savegame, rng, report, queuebie_registry):
    faction = player_savegame.player_faction
    sword = _sword(savegame=player_savegame, owner=faction)

    PlayerTurn(savegame=player_savegame, policy=POLICIES["aggressive"], rng=rng, report=report).hand_out_gear()

    faction.leader.refresh_from_db()
    assert faction.leader.weapon == sword
    assert report.items_equipped == 1


@pytest.mark.django_db
def test_build_raises_the_first_building_it_may(player_savegame, rng, report, queuebie_registry):
    TransactionFactory(faction=player_savegame.player_faction, amount=10_000)

    PlayerTurn(savegame=player_savegame, policy=POLICIES["aggressive"], rng=rng, report=report).build()

    assert report.built == [(1, "hall", 1)]


@pytest.mark.django_db
def test_build_passes_over_a_refused_building(player_savegame, rng, report, queuebie_registry):
    """The hall is at its top level, so the upgrade refusal sends the silver to the next in line."""
    town = player_savegame.player_faction.town
    town.hall = Hall.get_max_level()
    town.save()
    TransactionFactory(faction=player_savegame.player_faction, amount=10_000)

    PlayerTurn(savegame=player_savegame, policy=POLICIES["aggressive"], rng=rng, report=report).build()

    assert report.built == [(1, "sanctuary", 1)]


@pytest.mark.django_db
def test_build_keeps_silver_back(player_savegame, rng, report, queuebie_registry):
    """The marketplace, at 400 the cheapest, is affordable - but not and still leave the 150 standing."""
    TransactionFactory(faction=player_savegame.player_faction, amount=549)

    PlayerTurn(savegame=player_savegame, policy=POLICIES["aggressive"], rng=rng, report=report).build()

    assert report.built == []


@pytest.mark.django_db
def test_send_men_on_the_odd_job_sends_the_weakest_man_it_takes(player_savegame, rng, report, queuebie_registry):
    """The errand ahead of it on the board is passed over: the harness only ever takes the odd job."""
    faction = player_savegame.player_faction
    weak_warrior = WarriorFactory(faction=faction, strength=6)
    WarriorFactory(faction=faction, strength=12)
    QuestFactory(faction=faction, month=player_savegame.current_month, quest=DriveOffWolves.__name__)
    QuestFactory(faction=faction, month=player_savegame.current_month, quest=HarvestHands.__name__)

    PlayerTurn(
        savegame=player_savegame, policy=POLICIES["aggressive"], rng=rng, report=report
    ).send_men_on_the_odd_job()

    assert list(QuestContract.objects.get(faction=faction).assigned_warriors.all()) == [weak_warrior]
    assert report.sent_on_quests == 1


@pytest.mark.django_db
def test_send_men_on_the_odd_job_keeps_the_leader_home(player_savegame, rng, report, queuebie_registry):
    faction = player_savegame.player_faction
    QuestFactory(faction=faction, month=player_savegame.current_month, quest=HarvestHands.__name__)

    PlayerTurn(
        savegame=player_savegame, policy=POLICIES["aggressive"], rng=rng, report=report
    ).send_men_on_the_odd_job()

    assert QuestContract.objects.exists() is False
    assert report.sent_on_quests == 0


@pytest.mark.django_db
def test_march_without_a_target_stays_home(player_savegame, rng, report):
    result = PlayerTurn(savegame=player_savegame, policy=POLICIES["aggressive"], rng=rng, report=report).march()

    assert result is None
    assert Skirmish.objects.exists() is False


@pytest.mark.django_db
def test_march_takes_only_the_men_the_attack_form_would_offer(player_savegame, rng, report, queuebie_registry):
    """
    Who may march is the one rule that lives only in a form, so the band has to come from the same
    roster assessment the form validates against: the man who is down stays home.
    """
    faction = player_savegame.player_faction
    fit_man = WarriorFactory(faction=faction)
    WarriorFactory(faction=faction, condition=Warrior.ConditionChoices.CONDITION_UNCONSCIOUS)
    rival = FactionFactory(savegame=player_savegame)
    rival.leader = WarriorFactory(faction=rival)
    rival.save()

    PlayerTurn(savegame=player_savegame, policy=POLICIES["aggressive"], rng=rng, report=report).march()

    skirmish = Skirmish.objects.get()
    assert set(skirmish.attacking_warriors.values_list("id", flat=True)) == {faction.leader_id, fit_man.id}


@pytest.mark.django_db
def test_march_held_back_by_the_policy(player_savegame, rng, report):
    rival = FactionFactory(savegame=player_savegame)
    rival.leader = WarriorFactory(faction=rival)
    rival.save()

    result = PlayerTurn(savegame=player_savegame, policy=POLICIES["prudent"], rng=rng, report=report).march()

    assert result is None
    assert report.marches_held_back == 1


@pytest.mark.django_db
def test_march_lifts_the_herds_when_the_policy_holds_it_back_from_the_burh(
    player_savegame, rng, report, queuebie_registry
):
    """The rival has two men to the player's one, so "raider" goes after the herds instead of the burh."""
    rival = FactionFactory(savegame=player_savegame)
    rival.leader = WarriorFactory(faction=rival)
    rival.save()
    WarriorFactory(faction=rival)

    PlayerTurn(savegame=player_savegame, policy=POLICIES["raider"], rng=rng, report=report).march()

    assert Skirmish.objects.get().raid_kind == RaidKindChoices.LIFT_THE_HERDS
    assert report.herd_raids == 1


@pytest.mark.django_db
def test_march_leaves_men_home_until_the_march_is_affordable(player_savegame, rng, report, queuebie_registry):
    """Winterfylleth prices a march at 10 a man: 25 silver takes two of the three."""
    player_savegame.current_month = 7
    player_savegame.save()
    faction = player_savegame.player_faction
    first_man = WarriorFactory(faction=faction)
    WarriorFactory(faction=faction)
    TransactionFactory(faction=faction, amount=25)
    rival = FactionFactory(savegame=player_savegame)
    rival.leader = WarriorFactory(faction=rival)
    rival.save()

    PlayerTurn(savegame=player_savegame, policy=POLICIES["aggressive"], rng=rng, report=report).march()

    skirmish = Skirmish.objects.get()
    assert set(skirmish.attacking_warriors.values_list("id", flat=True)) == {faction.leader_id, first_man.id}


@pytest.mark.django_db
def test_march_unaffordable_even_for_the_leader(player_savegame, rng, report):
    player_savegame.current_month = 7
    player_savegame.save()
    rival = FactionFactory(savegame=player_savegame)
    rival.leader = WarriorFactory(faction=rival)
    rival.save()

    result = PlayerTurn(savegame=player_savegame, policy=POLICIES["aggressive"], rng=rng, report=report).march()

    assert result is None
    assert report.marches_unaffordable == 1


@pytest.mark.django_db
def test_fight_counts_a_fight_won(player_savegame, rng, report):
    skirmish = SkirmishFactory(
        attacking_faction=player_savegame.player_faction, victorious_faction=player_savegame.player_faction
    )

    result = PlayerTurn(savegame=player_savegame, policy=POLICIES["aggressive"], rng=rng, report=report).fight(
        skirmish=skirmish
    )

    assert result is None
    assert report.fights_won == 1


@pytest.mark.django_db
def test_fight_counts_a_fight_lost(player_savegame, rng, report):
    skirmish = SkirmishFactory(attacking_faction=player_savegame.player_faction)
    skirmish.victorious_faction = skirmish.defending_faction
    skirmish.save()

    PlayerTurn(savegame=player_savegame, policy=POLICIES["aggressive"], rng=rng, report=report).fight(skirmish=skirmish)

    assert report.fights_lost == 1


@pytest.mark.django_db
def test_fight_plays_rounds_on_the_players_side_as_the_defender(player_savegame, rng, report, queuebie_registry):
    """
    The player's side is found whichever side he stands on. One round is enough to show a round was
    fought for real: the counter moves on.
    """
    faction = player_savegame.player_faction
    skirmish = SkirmishFactory(defending_faction=faction, attacking_faction__savegame=player_savegame)
    skirmish.defending_warriors.add(faction.leader)
    skirmish.attacking_warriors.add(WarriorFactory(faction=skirmish.attacking_faction))

    PlayerTurn(savegame=player_savegame, policy=POLICIES["aggressive"], rng=rng, report=report, max_rounds=1).fight(
        skirmish=skirmish
    )

    skirmish.refresh_from_db()
    assert skirmish.current_round == 2


@pytest.mark.django_db
def test_fight_stops_when_a_side_has_nobody_to_field(player_savegame, rng, report):
    faction = player_savegame.player_faction
    skirmish = SkirmishFactory(attacking_faction=faction)
    skirmish.attacking_warriors.add(faction.leader)
    skirmish.defending_warriors.add(
        WarriorFactory(faction=skirmish.defending_faction, condition=Warrior.ConditionChoices.CONDITION_UNCONSCIOUS)
    )

    result = PlayerTurn(savegame=player_savegame, policy=POLICIES["aggressive"], rng=rng, report=report).fight(
        skirmish=skirmish
    )

    assert result == STOP_FIGHT_STUCK


@pytest.mark.django_db
def test_fight_stops_when_the_rounds_run_out(player_savegame, rng, report):
    skirmish = SkirmishFactory(attacking_faction=player_savegame.player_faction)

    result = PlayerTurn(
        savegame=player_savegame, policy=POLICIES["aggressive"], rng=rng, report=report, max_rounds=0
    ).fight(skirmish=skirmish)

    assert result == STOP_FIGHT_STUCK
