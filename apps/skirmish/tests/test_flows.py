import pytest
from queuebie.runner import handle_message

from apps.skirmish.choices.skirmish_action import SkirmishActionChoices
from apps.skirmish.messages.commands.warrior import IncreaseExperience
from apps.skirmish.messages.events.warrior import WarriorDefendedAllDamage
from apps.skirmish.models.battle_history import BattleHistory
from apps.skirmish.models.warrior import Warrior
from apps.skirmish.tests.factories.skirmish import SkirmishFactory
from apps.skirmish.tests.factories.warrior import WarriorFactory


@pytest.mark.django_db
def test_a_warrior_who_only_turtles_eventually_routs(queuebie_registry):
    """
    The chain that makes an unwinnable fight end, run for real rather than asserted handler by handler.

    Below a quarter of his health a warrior always picks a defensive stance, which doubles his defense
    and zeroes his attack. Once that defense outruns what the other side can hit for, nobody takes
    damage and nobody falls - and those were the only two things that moved morale. So the drain has
    to come from the stance itself, and it has to reach all the way to CONDITION_FLEEING, which the
    defeat check counts as "not healthy". Only a real queue run proves the three handlers between the
    block and the rout are actually wired to each other.

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
            attacker=attacker,
            attacker_damage=4,
            defender=exhausted_defender,
            defender_damage=20,
            defender_action=SkirmishActionChoices.DEFENSIVE_STANCE,
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
