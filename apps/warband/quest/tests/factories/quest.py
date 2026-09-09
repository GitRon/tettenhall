import factory
from factory.django import DjangoModelFactory

from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.quest.models.quest import Quest


class QuestFactory(DjangoModelFactory):
    class Meta:
        model = Quest

    name = factory.Sequence(lambda n: f"Quest {n}")
    loot = 200
    target_faction = factory.SubFactory(FactionFactory)
    difficulty = Quest.DifficultyChoices.DIFFICULTY_EASY
    # The top of the easy band the difficulty above carries, so a quest out of this factory is one
    # written against a target that can field a full war band
    expected_opposition = 5
