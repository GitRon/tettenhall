import pytest
from queuebie.runner import handle_message

from apps.skirmish.choices.skirmish_action import SkirmishActionChoices
from apps.skirmish.messages.events.warrior import WarriorDefendedAllDamage
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
    attacker = WarriorFactory(faction=skirmish.player_faction)
    exhausted_defender = WarriorFactory(
        faction=skirmish.non_player_faction, current_morale=2, max_morale=20, current_health=3
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
