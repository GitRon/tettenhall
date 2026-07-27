import factory
from factory.django import DjangoModelFactory

from apps.faction.tests.factories.faction import FactionFactory
from apps.quest.models.quest import Quest


class QuestFactory(DjangoModelFactory):
    class Meta:
        model = Quest

    name = factory.Sequence(lambda n: f"Quest {n}")
    loot = 200
    target_faction = factory.SubFactory(FactionFactory)
    difficulty = Quest.DifficultyChoices.DIFFICULTY_EASY
