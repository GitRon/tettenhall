from unittest import mock

import pytest
from queuebie.runner import handle_message

from apps.common.domain.dice import DiceNotation, DiceRoll
from apps.warband.item.models.item_type import ItemType
from apps.warband.item.tests.factories.item import ItemFactory
from apps.warband.item.tests.factories.item_type import ItemTypeFactory
from apps.warband.month.models.player_month_log import PlayerMonthLog
from apps.warband.skirmish.choices.blow_outcome import BlowOutcomeChoices
from apps.warband.skirmish.choices.initiative import InitiativeChoices
from apps.warband.skirmish.choices.skirmish_action import SkirmishActionChoices
from apps.warband.skirmish.domain.action_roll import ActionRoll
from apps.warband.skirmish.messages.commands.skirmish import WinSkirmish
from apps.warband.skirmish.messages.commands.warrior import IncreaseExperience, ReduceHealth
from apps.warband.skirmish.messages.events.warrior import WarriorDefendedAllDamage, WarriorTookDamage
from apps.warband.skirmish.models.battle_history import BattleHistory
from apps.warband.skirmish.models.skirmish_blow import SkirmishBlow
from apps.warband.skirmish.models.warrior import Warrior
from apps.warband.skirmish.tests.factories.skirmish import SkirmishFactory
from apps.warband.skirmish.tests.factories.skirmish_blow import SkirmishBlowFactory
from apps.warband.skirmish.tests.factories.warrior import WarriorFactory
from apps.warband.warrior.models.injury import Injury


@pytest.mark.django_db
def test_a_warrior_who_only_turtles_eventually_routs(queuebie_registry):
    """
    The chain that makes an unwinnable fight end, run for real rather than asserted handler by handler.

    Below a quarter of his health a warrior always picks a defensive stance, which zeroes his attack.
    Once both sides are there neither throws a blow, so nobody takes damage and nobody falls - and
    those were the only two things that moved morale. So the drain has to come from the stance itself,
    and it has to reach all the way to CONDITION_FLEEING, which the defeat check counts as "not
    healthy". Only a real queue run proves the three handlers between the block and the rout are
    actually wired to each other.

    Driven with a blow that was never thrown, because that is the state the damage service raises this
    event for: a positive attack keeps a share of itself past any defense.

    Set one round short of routing rather than looped: what matters is that the last point of morale
    turns into a rout, not how many rounds it took to get there.
    """
    skirmish = SkirmishFactory()
    attacker = WarriorFactory(faction=skirmish.attacking_faction)
    exhausted_defender = WarriorFactory(
        faction=skirmish.defending_faction, current_morale=2, max_morale=20, current_health=3
    )

    handle_message(
        WarriorDefendedAllDamage(
            skirmish=skirmish,
            round_number=1,
            attacker=attacker,
            attacker_action=SkirmishActionChoices.DEFENSIVE_STANCE,
            attack=ActionRoll(roll=None, value=0, outcome=BlowOutcomeChoices.OUTCOME_NOT_THROWN),
            defender=exhausted_defender,
            defender_action=SkirmishActionChoices.DEFENSIVE_STANCE,
            defense=ActionRoll(
                roll=DiceRoll(notation=DiceNotation(dice_string="1d4"), result=4),
                item_type=ItemTypeFactory(base_value="1d4", function=ItemType.FunctionChoices.FUNCTION_ARMOR),
                value=8,
            ),
            outcome=BlowOutcomeChoices.OUTCOME_NOT_THROWN,
            initiative=InitiativeChoices.INITIATIVE_WON_THE_ROLL,
        )
    )

    exhausted_defender.refresh_from_db()
    assert exhausted_defender.current_morale == 0
    assert exhausted_defender.condition == Warrior.ConditionChoices.CONDITION_FLEEING


@pytest.mark.django_db
def test_a_level_up_is_logged_before_the_growth_it_caused(queuebie_registry):
    """
    The two lines a level-up writes, in the order a player has to read them in.

    WarriorGainedLevel has two handlers - the logger and the one that starts the growth - and queuebie
    runs them in registration order, which is the order autodiscover() walked them: app configs, then
    os.listdir over handlers/events/. "battle_history.py" sorts before "warrior.py", so the level line
    is queued before the growth command and the log comes out right. Nothing enforces that ordering,
    and #40 was this same bug in the other direction, with a rout logged before the morale loss that
    caused it - so it is asserted here rather than trusted to a directory listing.

    Four hundred points from nothing crosses two thresholds at once, which also proves the second
    level-up is not swallowed, and that the two growths are told apart: the queue is FIFO, so both
    growths have already run by the time either line is written, and the wages quoted are 165 and 181
    only because the event carries the figure rather than reading it back off the shared instance.
    """
    skirmish = SkirmishFactory()
    warrior = WarriorFactory(
        faction=skirmish.attacking_faction,
        name="Beorn",
        experience=0,
        strength=10,
        dexterity=10,
        max_health=20,
        max_morale=20,
        monthly_salary=150,
    )

    handle_message(IncreaseExperience(skirmish=skirmish, warrior=warrior, increased_experience=400))

    assert list(BattleHistory.objects.order_by("id").values_list("message", flat=True)) == [
        "Beorn gained 400 experience.",
        "Beorn reached level 2.",
        "Beorn reached level 3.",
        "Beorn grew stronger: strength +1, dexterity +1, health +2, morale +2 — and now costs 165 silver a month.",
        "Beorn grew stronger: strength +1, dexterity +1, health +2, morale +2 — and now costs 181 silver a month.",
    ]


@pytest.mark.django_db
def test_a_knockout_marks_the_man_without_the_bus_reading_the_database(queuebie_registry):
    """
    A beating carried all the way through the queue, which is the only level that proves it works.

    The chain crosses the bus twice - the command that takes his last points raises
    WarriorWasIncapacitated, an event handler relays it as InflictInjury, and that command's handler
    rolls and writes the row - and the middle hop runs behind strict mode's database blocker. Every
    unit test in the suite calls its handler directly, where the blocker is not applied at all
    (docs/patterns/strict-mode.md says so in as many words), so a relay that reaches for anything it
    was not handed passes every one of them and raises the first time a real man goes down.

    It did. "reduce_current_health" refreshes the warrior from the database one handler earlier,
    which drops his cached faction, so building the command with "warrior.faction" was a query in the
    one place that may not make one - and the whole fight rolled back with "Database access is
    disabled in this context." His faction is read in the command handler now, and this is the test
    that says so.

    Twenty-two points against twenty health leaves him two past nothing, inside the 50% band that
    tells a corpse from a captive. The roll is patched to land, because whether he keeps something is
    not what this is about.
    """
    skirmish = SkirmishFactory(month=3)
    attacker = WarriorFactory(faction=skirmish.attacking_faction)
    defender = WarriorFactory(faction=skirmish.defending_faction, current_health=20, max_health=20)

    with mock.patch("apps.warband.warrior.services.injury.random.random", return_value=0.0):
        handle_message(ReduceHealth(skirmish=skirmish, warrior=defender, attacker=attacker, lost_health=22))

    assert Injury.objects.for_warrior(warrior_id=defender.id).count() == 1


@pytest.mark.django_db
def test_a_fight_that_shakes_a_man_changes_him_and_tells_the_player_so(queuebie_registry):
    """
    A won fight carried through the queue to the trait it earned and the line the month log keeps.

    The relay off SkirmishFinished runs behind strict mode's blocker and carries nothing but the fight;
    which men count is read in the command handler. Only a queue run proves the relay reads nothing,
    and that the event the handler ends in reaches the month log.
    """
    skirmish = SkirmishFactory(month=3)
    player_faction = skirmish.attacking_faction
    player_faction.savegame.player_faction = player_faction
    player_faction.savegame.save()
    warrior = WarriorFactory(faction=player_faction, name="Sven")
    skirmish.attacking_warriors.add(warrior)
    skirmish.defending_warriors.add(
        WarriorFactory(faction=skirmish.defending_faction, condition=Warrior.ConditionChoices.CONDITION_FLEEING)
    )
    SkirmishBlowFactory.create_batch(4, skirmish=skirmish, defender=warrior, outcome=BlowOutcomeChoices.OUTCOME_HIT)

    handle_message(WinSkirmish(skirmish=skirmish, victorious_faction=player_faction, month=3))

    assert list(warrior.traits.values_list("type__hook", flat=True)) == ["shaken"]
    assert PlayerMonthLog.objects.filter(
        kind=PlayerMonthLog.KindChoices.KIND_WARRIOR_CHANGED, title="Sven came back from the fight a different man."
    ).exists()


def _first_blow(*, skirmish, attacker, defender, damage: int) -> WarriorTookDamage:
    return WarriorTookDamage(
        skirmish=skirmish,
        round_number=1,
        attacker=attacker,
        attacker_action=SkirmishActionChoices.SIMPLE_ATTACK,
        attack=ActionRoll(
            roll=DiceRoll(notation=DiceNotation(dice_string="2d6"), result=damage),
            item_type=ItemTypeFactory(base_value="2d6", function=ItemType.FunctionChoices.FUNCTION_WEAPON),
            value=damage,
        ),
        defender=defender,
        defender_action=SkirmishActionChoices.SIMPLE_ATTACK,
        defense=ActionRoll(
            roll=DiceRoll(notation=DiceNotation(dice_string="1d4"), result=1),
            item_type=ItemTypeFactory(base_value="1d4", function=ItemType.FunctionChoices.FUNCTION_ARMOR),
            value=0,
        ),
        damage=damage,
        initiative=InitiativeChoices.INITIATIVE_WON_THE_ROLL,
    )


@pytest.mark.django_db
def test_the_slower_man_of_a_pair_strikes_back_once_the_first_blow_has_landed(queuebie_registry):
    """
    The counter is raised off the first blow's result, and only a real queue run shows it is actually
    thrown - the blow record it leaves is written three hops further down.
    """
    skirmish = SkirmishFactory()
    attacker = WarriorFactory(faction=skirmish.attacking_faction)
    defender = WarriorFactory(faction=skirmish.defending_faction, current_health=40, max_health=40)

    handle_message(_first_blow(skirmish=skirmish, attacker=attacker, defender=defender, damage=5))

    assert SkirmishBlow.objects.filter(attacker=defender, defender=attacker).count() == 1


@pytest.mark.django_db
def test_a_man_the_first_blow_puts_down_does_not_strike_back(queuebie_registry):
    """
    What the counter's position in the queue is for. It is declared below the health handler, so it
    drains behind "ReduceHealth" and sees the man already down. Raised beside the first blow instead, it
    would drain first, and a man lying senseless would swing back at the one who felled him.
    """
    skirmish = SkirmishFactory()
    attacker = WarriorFactory(faction=skirmish.attacking_faction)
    defender = WarriorFactory(faction=skirmish.defending_faction, current_health=5, max_health=40)

    handle_message(_first_blow(skirmish=skirmish, attacker=attacker, defender=defender, damage=8))

    assert SkirmishBlow.objects.filter(attacker=defender).count() == 0


@pytest.mark.django_db
def test_a_rival_whose_whole_band_is_taken_comes_out_of_it_led_by_a_levy(queuebie_registry):
    """
    The chain from a lost defence to a rival still in the war, run for real: the win captures every man
    lying on the field, each capture asks the defeat handler for a seat, the last one finds the roster
    empty, the fyrd raises a levy, and the hand-out that hangs off his recruitment arms him out of the
    stores. Four hops apart in the registry, and the capture order decides which of them sees whom.

    The rival's leader and his one man are both down, so both are taken, and its fyrd has one man left.
    """
    skirmish = SkirmishFactory()
    player_faction = skirmish.attacking_faction
    player_faction.savegame.player_faction = player_faction
    player_faction.savegame.save()
    rival = skirmish.defending_faction
    rival.fyrd_reserve = 1
    rival.leader = WarriorFactory(faction=rival, condition=Warrior.ConditionChoices.CONDITION_UNCONSCIOUS)
    rival.save()
    comrade = WarriorFactory(faction=rival, condition=Warrior.ConditionChoices.CONDITION_UNCONSCIOUS)
    skirmish.attacking_warriors.add(WarriorFactory(faction=player_faction))
    skirmish.defending_warriors.add(rival.leader, comrade)
    mail = ItemFactory(
        savegame=rival.savegame,
        owner=rival,
        type=ItemTypeFactory(function=ItemType.FunctionChoices.FUNCTION_ARMOR, base_value="6d6"),
    )

    # The levy comes from the fields empty-handed: a levy rolls his own gear one time in ten, and one
    # who brought armour no worse than the mail keeps it, so the hand-out would have nothing to do
    with mock.patch("apps.warband.warrior.services.generators.warrior.base.random.uniform", return_value=1.0):
        handle_message(WinSkirmish(skirmish=skirmish, victorious_faction=player_faction, month=1))

    rival.refresh_from_db()
    assert (rival.is_defeated, rival.fyrd_reserve, rival.leader.faction, rival.leader.armor) == (False, 0, rival, mail)
