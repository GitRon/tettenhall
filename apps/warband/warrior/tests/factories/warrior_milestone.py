import factory
from factory.django import DjangoModelFactory

from apps.warband.skirmish.tests.factories.warrior import WarriorFactory
from apps.warband.warrior.choices.warrior_milestone import JoinedWayChoices, MilestoneKindChoices
from apps.warband.warrior.models.warrior_milestone import WarriorMilestone


class WarriorMilestoneFactory(DjangoModelFactory):
    class Meta:
        model = WarriorMilestone

    warrior = factory.SubFactory(WarriorFactory)
    kind = MilestoneKindChoices.JOINED
    month = 1
    faction = factory.SelfAttribute("warrior.faction")
    joined_way = JoinedWayChoices.DRAFTED
