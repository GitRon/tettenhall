import factory
from factory.django import DjangoModelFactory

from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.skirmish.models.warrior import Warrior
from apps.warband.warrior.services.nickname import draw_nickname_state


class WarriorFactory(DjangoModelFactory):
    class Meta:
        model = Warrior

    name = factory.Sequence(lambda n: f"Warrior {n}")
    faction = factory.SubFactory(FactionFactory)
    # Keep warrior, faction and savegame consistent instead of creating a second savegame
    savegame = factory.SelfAttribute("faction.savegame")
    culture = factory.SelfAttribute("faction.culture")

    strength = 10
    # A warrior sitting exactly at his baseline deals his weapon's full damage, which is what the
    # arithmetic in most of the suite is written against
    strength_baseline = 10
    # A middling spread and the mercenary's floor. With both stats sitting on the baseline, well
    # clear of that floor, it leaves the factory's warrior an ordinary man: no test's warrior picks
    # up an epithet he was never written to have
    stats_spread = 5
    stats_minimum = 3
    dexterity = 10
    current_health = 20
    max_health = 20
    current_morale = 20
    max_morale = 20
    # Every baseline matches the value beside it, so the factory's warrior sits exactly at his kind's
    # mean in all four attributes and earns no epithet. A test that wants one moves one attribute
    health_baseline = 20
    health_spread = 10
    morale_baseline = 20
    morale_spread = 5

    @factory.lazy_attribute
    def nickname_state(self) -> int | None:
        """
        Drawn from the attributes above the way the generator draws it, so that moving one attribute
        is all a test has to do to make a man worth naming.

        Through an unsaved warrior rather than four "AttributeDraw"s built here, because which
        baseline and which spread belong to which attribute is exactly what several tests in the suite
        exist to pin - a second copy of that pairing could agree with itself and disagree with the
        model.

        Passing "nickname_state" outright is how a test pins a man to an epithet his attributes no
        longer support, which is the whole point of the column.
        """
        return draw_nickname_state(
            **Warrior(
                strength=self.strength,
                dexterity=self.dexterity,
                strength_baseline=self.strength_baseline,
                stats_spread=self.stats_spread,
                stats_minimum=self.stats_minimum,
                max_health=self.max_health,
                health_baseline=self.health_baseline,
                health_spread=self.health_spread,
                max_morale=self.max_morale,
                morale_baseline=self.morale_baseline,
                morale_spread=self.morale_spread,
            ).attribute_draws
        )
