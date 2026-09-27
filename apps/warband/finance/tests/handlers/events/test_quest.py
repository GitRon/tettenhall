from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.finance.handlers.events.quest import handle_pay_march_cost_for_quest
from apps.warband.finance.messages.commands.transaction import CreateTransaction
from apps.warband.quest.messages.events.quest import QuestAccepted
from apps.warband.quest.tests.factories.quest import QuestFactory
from apps.warband.quest.tests.factories.quest_contract import QuestContractFactory
from apps.warband.skirmish.tests.factories.warrior import WarriorFactory


def test_handle_pay_march_cost_for_quest_in_the_yule_month():
    """Month 9 is Ærra Geola, where the winter march costs 15 a man."""
    accepting_faction = FactionFactory.build()
    target_faction = FactionFactory.build(name="Tamworth")

    result = handle_pay_march_cost_for_quest(
        context=QuestAccepted(
            accepting_faction=accepting_faction,
            target_faction=target_faction,
            quest=QuestFactory.build(),
            quest_contract=QuestContractFactory.build(),
            assigned_warriors=[WarriorFactory.build(), WarriorFactory.build()],
            target_warriors=[WarriorFactory.build()],
            month=9,
        )
    )

    assert result == CreateTransaction(
        faction=accepting_faction, amount=-30, reason="Winter march on Tamworth", month=9
    )


def test_handle_pay_march_cost_for_quest_in_summer():
    result = handle_pay_march_cost_for_quest(
        context=QuestAccepted(
            accepting_faction=FactionFactory.build(),
            target_faction=FactionFactory.build(),
            quest=QuestFactory.build(),
            quest_contract=QuestContractFactory.build(),
            assigned_warriors=[WarriorFactory.build()],
            target_warriors=[WarriorFactory.build()],
            month=3,
        )
    )

    assert result is None
