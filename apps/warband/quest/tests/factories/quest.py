import factory
from factory.django import DjangoModelFactory

from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.quest.models.quest import Quest
from apps.warband.quest.quests.harvest_hands import HarvestHands


class QuestFactory(DjangoModelFactory):
    class Meta:
        model = Quest

    faction = factory.SubFactory(FactionFactory)
    month = 1
    # The odd job, because it takes a single man: a quest out of this factory can be sent on by any
    # faction with one warrior
    quest = HarvestHands.__name__
    title = HarvestHands.TITLE
    body = HarvestHands.BODY
