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
from apps.warband.town.buildings import BUILDINGS
from apps.warband.town.buildings.hall import Hall
from apps.warband.town.buildings.marketplace import Marketplace
from apps.warband.town.buildings.sanctuary import Sanctuary
from apps.warband.town.models import Town
from scripts.playtest.player import BUILD_ORDER, STOP_FIGHT_STUCK, PlayerTurn
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
def test_build_raises_the_weaponsmith_first_for_a_reforging_player(player_savegame, rng, report, queuebie_registry):
    TransactionFactory(faction=player_savegame.player_faction, amount=10_000)

    PlayerTurn(savegame=player_savegame, policy=POLICIES["aggressive"], rng=rng, report=report, reforging=True).build()

    assert report.built == [(1, "weaponsmith", 1)]


@pytest.mark.django_db
def test_build_keeps_the_sanctuary_first_for_a_player_who_tends_and_reforges(
    player_savegame, rng, report, queuebie_registry
):
    TransactionFactory(faction=player_savegame.player_faction, amount=10_000)

    PlayerTurn(
        savegame=player_savegame, policy=POLICIES["aggressive"], rng=rng, report=report, tending=True, reforging=True
    ).build()

    assert report.built == [(1, "sanctuary", 1)]


@pytest.mark.django_db
def test_build_keeps_silver_back(player_savegame, rng, report, queuebie_registry):
    """The marketplace, at 400 the cheapest, is affordable - but not and still leave the 150 standing."""
    TransactionFactory(faction=player_savegame.player_faction, amount=549)

    PlayerTurn(savegame=player_savegame, policy=POLICIES["aggressive"], rng=rng, report=report).build()

    assert report.built == []


@pytest.mark.django_db
def test_send_men_on_the_steady_work_sends_the_weakest_man_it_takes(player_savegame, rng, report, queuebie_registry):
    """The errand ahead of it on the board is passed over: the harness only ever takes the steady work."""
    faction = player_savegame.player_faction
    weak_warrior = WarriorFactory(faction=faction, strength=6)
    WarriorFactory(faction=faction, strength=12)
    QuestFactory(faction=faction, month=player_savegame.current_month, quest=DriveOffWolves.__name__)
    QuestFactory(faction=faction, month=player_savegame.current_month, quest=HarvestHands.__name__)

    PlayerTurn(
        savegame=player_savegame, policy=POLICIES["aggressive"], rng=rng, report=report
    ).send_men_on_the_steady_work()

    assert list(QuestContract.objects.get(faction=faction).assigned_warriors.all()) == [weak_warrior]
    assert report.sent_on_quests == 1


@pytest.mark.django_db
def test_send_men_on_the_steady_work_keeps_the_leader_home(player_savegame, rng, report, queuebie_registry):
    faction = player_savegame.player_faction
    QuestFactory(faction=faction, month=player_savegame.current_month, quest=HarvestHands.__name__)

    PlayerTurn(
        savegame=player_savegame, policy=POLICIES["aggressive"], rng=rng, report=report
    ).send_men_on_the_steady_work()

    assert QuestContract.objects.exists() is False
    assert report.sent_on_quests == 0


@pytest.mark.django_db
def test_build_raises_the_sanctuary_first_for_a_tending_player(player_savegame, rng, report, queuebie_registry):
    TransactionFactory(faction=player_savegame.player_faction, amount=10_000)

    PlayerTurn(savegame=player_savegame, policy=POLICIES["aggressive"], rng=rng, report=report, tending=True).build()

    assert report.built == [(1, "sanctuary", 1)]


@pytest.mark.django_db
def test_play_tends_the_wounded_only_for_a_tending_player(player_savegame, rng, report, queuebie_registry):
    """
    Before the pub and the shop, so the purse they spend down is still there to pay the sanctuary.
    """
    faction = player_savegame.player_faction
    faction.town.sanctuary = Town.SanctuaryChoices.SANCTUARY_SMALL
    faction.town.save()
    WarriorFactory(faction=faction, current_health=10, max_health=40)
    TransactionFactory(faction=faction, amount=300)

    PlayerTurn(savegame=player_savegame, policy=POLICIES["prudent"], rng=rng, report=report, tending=True).play()

    assert report.warriors_tended == 1


@pytest.mark.django_db
def test_tend_the_wounded_mends_every_man_the_purse_covers(player_savegame, rng, report, queuebie_registry):
    faction = player_savegame.player_faction
    faction.town.sanctuary = Town.SanctuaryChoices.SANCTUARY_SMALL
    faction.town.save()
    badly_hurt = WarriorFactory(faction=faction, current_health=10, max_health=40)
    scratched = WarriorFactory(faction=faction, current_health=30, max_health=40)
    TransactionFactory(faction=faction, amount=10_000)

    PlayerTurn(savegame=player_savegame, policy=POLICIES["aggressive"], rng=rng, report=report).tend_the_wounded()

    assert [Warrior.objects.get(id=w.id).current_health for w in (badly_hurt, scratched)] == [40, 40]
    assert report.warriors_tended == 2


@pytest.mark.django_db
def test_tend_the_wounded_passes_over_a_man_too_dear_to_mend(player_savegame, rng, report, queuebie_registry):
    """
    Thirty points cost 150 and would eat into the 150 kept back; the ten behind him cost 50 and do not.
    """
    faction = player_savegame.player_faction
    faction.town.sanctuary = Town.SanctuaryChoices.SANCTUARY_SMALL
    faction.town.save()
    badly_hurt = WarriorFactory(faction=faction, current_health=10, max_health=40)
    scratched = WarriorFactory(faction=faction, current_health=30, max_health=40)
    TransactionFactory(faction=faction, amount=200)

    PlayerTurn(savegame=player_savegame, policy=POLICIES["aggressive"], rng=rng, report=report).tend_the_wounded()

    assert [Warrior.objects.get(id=w.id).current_health for w in (badly_hurt, scratched)] == [10, 40]


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
    """
    Three men against two and the burh's two of the fyrd is too few for the burh, and enough for the
    herdsman with none of the rival's own men expected at the herds.
    """
    WarriorFactory.create_batch(2, faction=player_savegame.player_faction)
    rival = FactionFactory(savegame=player_savegame)
    rival.leader = WarriorFactory(faction=rival)
    rival.save()
    WarriorFactory(faction=rival)

    PlayerTurn(savegame=player_savegame, policy=POLICIES["raider"], rng=rng, report=report).march()

    assert Skirmish.objects.get().raid_kind == RaidKindChoices.LIFT_THE_HERDS
    assert report.herd_raids == 1


@pytest.mark.django_db
def test_march_held_back_from_the_herds_too_when_even_the_herdsmen_outnumber_the_band(player_savegame, rng, report):
    """One man against the herdsman and the one of the rival's three men expected at the herds."""
    rival = FactionFactory(savegame=player_savegame)
    rival.leader = WarriorFactory(faction=rival)
    rival.save()
    WarriorFactory.create_batch(2, faction=rival)

    result = PlayerTurn(savegame=player_savegame, policy=POLICIES["raider"], rng=rng, report=report).march()

    assert result is None
    assert report.marches_held_back == 1


@pytest.mark.django_db
def test_march_held_back_from_a_burh_whose_fyrd_turns_out(player_savegame, rng, report):
    """Two men outnumber the rival's one, and not the one with the burh's two of the fyrd beside him."""
    WarriorFactory(faction=player_savegame.player_faction)
    rival = FactionFactory(savegame=player_savegame)
    rival.leader = WarriorFactory(faction=rival)
    rival.save()

    result = PlayerTurn(savegame=player_savegame, policy=POLICIES["even"], rng=rng, report=report).march()

    assert result is None
    assert report.marches_held_back == 1


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


@pytest.mark.django_db
def test_play_calls_a_geld_before_the_draft_only_for_a_geld_player(player_savegame, rng, report, queuebie_registry):
    """
    Before the draft, or the draft would have raised every name the village could pay with.
    """
    faction = player_savegame.player_faction
    faction.fyrd_reserve = 2
    faction.save()

    PlayerTurn(savegame=player_savegame, policy=POLICIES["prudent"], rng=rng, report=report, geld=True).play()

    assert (report.gelds_called, report.drafted) == (1, 1)


@pytest.mark.django_db
def test_call_a_geld_leaves_the_village_alone_while_the_purse_holds_out(
    player_savegame, rng, report, queuebie_registry
):
    faction = player_savegame.player_faction
    faction.fyrd_reserve = 2
    faction.save()
    TransactionFactory(faction=faction, amount=150)

    PlayerTurn(savegame=player_savegame, policy=POLICIES["aggressive"], rng=rng, report=report).call_a_geld()

    assert report.gelds_called == 0


@pytest.mark.django_db
def test_call_a_geld_passes_over_a_refused_geld(player_savegame, rng, report, queuebie_registry):
    PlayerTurn(savegame=player_savegame, policy=POLICIES["aggressive"], rng=rng, report=report).call_a_geld()

    assert report.gelds_called == 0


@pytest.mark.django_db
def test_play_leaves_the_village_alone_for_a_player_who_does_not_geld(player_savegame, rng, report, queuebie_registry):
    faction = player_savegame.player_faction
    faction.fyrd_reserve = 2
    faction.save()

    PlayerTurn(savegame=player_savegame, policy=POLICIES["prudent"], rng=rng, report=report).play()

    assert (report.gelds_called, report.drafted) == (0, 2)


def _reforging_faction(player_savegame: Savegame) -> Faction:
    faction = player_savegame.player_faction
    Town.objects.filter(faction=faction).update(weaponsmith=Town.WeaponsmithChoices.WEAPONSMITH_LARGE)
    faction.town.refresh_from_db()
    TransactionFactory(faction=faction, amount=1000)
    return faction


def _worn_piece(*, faction: Faction, condition: int) -> Item:
    return ItemFactory(savegame=faction.savegame, owner=faction, condition=condition, modifier=0, price=70)


@pytest.mark.django_db
def test_reforge_gear_reworks_the_weakest_piece_on_the_strongest_man(player_savegame, rng, report, queuebie_registry):
    faction = _reforging_faction(player_savegame)
    rusty = _worn_piece(faction=faction, condition=Item.ConditionChoices.CONDITION_RUSTY)
    WarriorFactory(
        faction=faction,
        strength=20,
        weapon=_worn_piece(faction=faction, condition=Item.ConditionChoices.CONDITION_TRADITIONAL),
        armor=rusty,
    )
    weak_mans_piece = _worn_piece(faction=faction, condition=Item.ConditionChoices.CONDITION_RUSTY)
    WarriorFactory(faction=faction, strength=5, weapon=weak_mans_piece)

    PlayerTurn(savegame=player_savegame, policy=POLICIES["prudent"], rng=rng, report=report).reforge_gear()

    rusty.refresh_from_db()
    assert (rusty.condition, report.items_reforged) == (Item.ConditionChoices.CONDITION_CHEAP, 1)


@pytest.mark.django_db
def test_reforge_gear_passes_over_a_piece_the_forge_cannot_improve(player_savegame, rng, report, queuebie_registry):
    faction = _reforging_faction(player_savegame)
    WarriorFactory(
        faction=faction,
        strength=20,
        weapon=_worn_piece(faction=faction, condition=Item.ConditionChoices.CONDITION_SUPERIOR),
    )
    weak_mans_piece = _worn_piece(faction=faction, condition=Item.ConditionChoices.CONDITION_RUSTY)
    WarriorFactory(faction=faction, strength=5, weapon=weak_mans_piece)

    PlayerTurn(savegame=player_savegame, policy=POLICIES["prudent"], rng=rng, report=report).reforge_gear()

    weak_mans_piece.refresh_from_db()
    assert weak_mans_piece.condition == Item.ConditionChoices.CONDITION_CHEAP


@pytest.mark.django_db
def test_play_reforges_only_for_a_reforging_player(player_savegame, rng, report, queuebie_registry):
    faction = _reforging_faction(player_savegame)
    WarriorFactory(
        faction=faction, weapon=_worn_piece(faction=faction, condition=Item.ConditionChoices.CONDITION_RUSTY)
    )

    PlayerTurn(savegame=player_savegame, policy=POLICIES["prudent"], rng=rng, report=report).play()

    assert report.items_reforged == 0


def _next_rung_costs(*, town: Town, building_type: str) -> int:
    return BUILDINGS[building_type].get_building_by_type(building_type=getattr(town, building_type) + 1).BUILDING_COSTS


def _top_out(*, town: Town, building_types: tuple[str, ...]) -> None:
    Town.objects.filter(id=town.id).update(
        **{building_type: BUILDINGS[building_type].get_max_level() for building_type in building_types}
    )
    town.refresh_from_db()


def _mercenary_in_the_pub(*, faction: Faction) -> Warrior:
    mercenary = WarriorFactory(faction=None, savegame=faction.savegame, culture=faction.culture)
    faction.available_mercenaries.add(mercenary)
    return mercenary


def _saving_turn(*, savegame: Savegame, rng, report, policy: str = "aggressive") -> PlayerTurn:
    return PlayerTurn(savegame=savegame, policy=POLICIES[policy], rng=rng, report=report, saving=True)


@pytest.mark.django_db
def test_hire_from_the_pub_keeps_the_next_building_back_for_a_saving_player(
    player_savegame, rng, report, queuebie_registry
):
    """The 150 alone would let him hire the man, but not and still pay for the next rung of the hall."""
    faction = player_savegame.player_faction
    mercenary = _mercenary_in_the_pub(faction=faction)
    hall_costs = _next_rung_costs(town=faction.town, building_type=Hall.BUILDING_NAME)
    TransactionFactory(faction=faction, amount=mercenary.hiring_price + 150 + hall_costs - 1)
    turn = _saving_turn(savegame=player_savegame, rng=rng, report=report)

    turn.hire_from_the_pub()

    mercenary.refresh_from_db()
    assert (mercenary.faction, report.hired, turn.held_back_by_saving) == (None, 0, True)


@pytest.mark.django_db
def test_hire_from_the_pub_hires_above_the_next_building_for_a_saving_player(
    player_savegame, rng, report, queuebie_registry
):
    faction = player_savegame.player_faction
    mercenary = _mercenary_in_the_pub(faction=faction)
    hall_costs = _next_rung_costs(town=faction.town, building_type=Hall.BUILDING_NAME)
    TransactionFactory(faction=faction, amount=mercenary.hiring_price + 150 + hall_costs)
    turn = _saving_turn(savegame=player_savegame, rng=rng, report=report)

    turn.hire_from_the_pub()

    assert (report.hired, turn.held_back_by_saving) == (1, False)


@pytest.mark.django_db
def test_hire_from_the_pub_is_not_held_back_by_the_saving_when_the_150_alone_stop_him(
    player_savegame, rng, report, queuebie_registry
):
    faction = player_savegame.player_faction
    mercenary = _mercenary_in_the_pub(faction=faction)
    TransactionFactory(faction=faction, amount=mercenary.hiring_price + 149)
    turn = _saving_turn(savegame=player_savegame, rng=rng, report=report)

    turn.hire_from_the_pub()

    assert (report.hired, turn.held_back_by_saving) == (0, False)


@pytest.mark.django_db
def test_buy_from_the_shop_keeps_the_next_building_back_for_a_saving_player(
    player_savegame, rng, report, queuebie_registry
):
    faction = player_savegame.player_faction
    sword = _sword(savegame=player_savegame)
    faction.available_items.add(sword)
    hall_costs = _next_rung_costs(town=faction.town, building_type=Hall.BUILDING_NAME)
    TransactionFactory(faction=faction, amount=60 + 150 + hall_costs - 1)
    turn = _saving_turn(savegame=player_savegame, rng=rng, report=report)

    turn.buy_from_the_shop()

    sword.refresh_from_db()
    assert (sword.owner, report.items_bought, turn.held_back_by_saving) == (None, 0, True)


@pytest.mark.django_db
def test_buy_from_the_shop_buys_above_the_next_building_for_a_saving_player(
    player_savegame, rng, report, queuebie_registry
):
    faction = player_savegame.player_faction
    faction.available_items.add(_sword(savegame=player_savegame))
    hall_costs = _next_rung_costs(town=faction.town, building_type=Hall.BUILDING_NAME)
    TransactionFactory(faction=faction, amount=60 + 150 + hall_costs)
    turn = _saving_turn(savegame=player_savegame, rng=rng, report=report)

    turn.buy_from_the_shop()

    assert (report.items_bought, turn.held_back_by_saving) == (1, False)


@pytest.mark.django_db
def test_build_raises_only_the_building_a_saving_player_saves_for(player_savegame, rng, report, queuebie_registry):
    """The marketplace further down is affordable, and would spend what he put by for the hall."""
    town = player_savegame.player_faction.town
    hall_costs = _next_rung_costs(town=town, building_type=Hall.BUILDING_NAME)
    assert _next_rung_costs(town=town, building_type=Marketplace.BUILDING_NAME) < hall_costs
    TransactionFactory(faction=player_savegame.player_faction, amount=150 + hall_costs - 1)

    _saving_turn(savegame=player_savegame, rng=rng, report=report).build()

    assert report.built == []


@pytest.mark.django_db
def test_saving_moves_on_to_the_next_building_once_the_first_is_at_its_top(
    player_savegame, rng, report, queuebie_registry
):
    """With the hall at its top level the sanctuary is next, and only its rung is kept back from the pub."""
    faction = player_savegame.player_faction
    _top_out(town=faction.town, building_types=(Hall.BUILDING_NAME,))
    mercenary = _mercenary_in_the_pub(faction=faction)
    sanctuary_costs = _next_rung_costs(town=faction.town, building_type=Sanctuary.BUILDING_NAME)
    TransactionFactory(faction=faction, amount=mercenary.hiring_price + 150 + sanctuary_costs)
    turn = _saving_turn(savegame=player_savegame, rng=rng, report=report)

    turn.hire_from_the_pub()
    turn.build()

    assert (report.hired, report.built) == (1, [(1, Sanctuary.BUILDING_NAME, 1)])


@pytest.mark.django_db
def test_saving_keeps_nothing_back_at_the_top_of_the_ladder(player_savegame, rng, report, queuebie_registry):
    faction = player_savegame.player_faction
    _top_out(town=faction.town, building_types=BUILD_ORDER)
    mercenary = _mercenary_in_the_pub(faction=faction)
    TransactionFactory(faction=faction, amount=mercenary.hiring_price + 150)
    turn = _saving_turn(savegame=player_savegame, rng=rng, report=report)

    turn.hire_from_the_pub()
    turn.build()

    assert (report.hired, report.built, turn.held_back_by_saving) == (1, [], False)


@pytest.mark.django_db
def test_play_counts_a_month_the_saving_held_the_pub_back(player_savegame, rng, report, queuebie_registry):
    faction = player_savegame.player_faction
    mercenary = _mercenary_in_the_pub(faction=faction)
    TransactionFactory(faction=faction, amount=mercenary.hiring_price + 150)

    _saving_turn(savegame=player_savegame, rng=rng, report=report, policy="prudent").play()

    assert (report.hired, report.months_saving) == (0, 1)


@pytest.mark.django_db
def test_play_keeps_nothing_back_for_a_player_who_does_not_save(player_savegame, rng, report, queuebie_registry):
    faction = player_savegame.player_faction
    mercenary = _mercenary_in_the_pub(faction=faction)
    TransactionFactory(faction=faction, amount=mercenary.hiring_price + 150)

    PlayerTurn(savegame=player_savegame, policy=POLICIES["prudent"], rng=rng, report=report).play()

    assert (report.hired, report.months_saving) == (1, 0)
