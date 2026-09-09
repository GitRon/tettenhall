import factory
from factory.django import DjangoModelFactory

from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.quest.models.quest_contract import QuestContract
from apps.warband.quest.tests.factories.quest import QuestFactory


class QuestContractFactory(DjangoModelFactory):
    class Meta:
        model = QuestContract

    faction = factory.SubFactory(FactionFactory)
    # Keep the quest target inside the same savegame as the signing faction
    quest = factory.SubFactory(QuestFactory, target_faction__savegame=factory.SelfAttribute("...faction.savegame"))
    accepted_in_month = 1
    skirmish = None
