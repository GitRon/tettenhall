import factory
from factory.django import DjangoModelFactory

from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.quest.models.quest_contract import QuestContract
from apps.warband.quest.quests.harvest_hands import HarvestHands


class QuestContractFactory(DjangoModelFactory):
    class Meta:
        model = QuestContract

    faction = factory.SubFactory(FactionFactory)
    quest = HarvestHands.__name__
    title = HarvestHands.TITLE
    accepted_in_month = 1
    resolved_in_month = None

    @factory.post_generation
    def assigned_warriors(self, create, extracted, **kwargs):
        if create and extracted:
            self.assigned_warriors.add(*extracted)
