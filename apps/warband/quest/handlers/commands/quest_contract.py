from queuebie import message_registry
from queuebie.messages import Event

from apps.warband.quest.messages.commands.quest_contract import BringQuestContractsHome
from apps.warband.quest.messages.events.quest_contract import QuestContractLapsed, QuestContractReturned
from apps.warband.quest.models.quest_contract import QuestContract
from apps.warband.quest.quests import QUESTS_BY_NAME


@message_registry.register_command(command=BringQuestContractsHome)
def handle_bring_quest_contracts_home(*, context: BringQuestContractsHome) -> list[Event]:
    """
    Bring every errand the faction sent men on before this month home, and draw what each brought.

    Asked of the men still on the roster when it lands, not of the men who set out: a man sent can be
    gone by now, and only the ones who are still the faction's share in what came back. A quest whose
    men are all gone lapses with a line of its own.

    Runs as the month opens, ahead of the salary run, so a man who walks out unpaid this month comes
    home first and leaves afterwards.
    """
    messages = []

    for quest_contract in QuestContract.objects.filter(faction=context.faction).still_away(month=context.month):
        # The month turn that lands this write is the one that brings the men home; a second one
        # overlapping it finds the contract resolved and leaves it alone
        if not QuestContract.objects.mark_resolved(quest_contract=quest_contract, month=context.month):
            continue

        warriors = list(
            quest_contract.assigned_warriors.filter(faction_id=context.faction.id).exclude_dead().order_by("id")
        )

        if not warriors:
            messages.append(
                QuestContractLapsed(faction=context.faction, quest_contract=quest_contract, month=context.month)
            )
            continue

        messages.append(
            QuestContractReturned(
                faction=context.faction,
                quest_contract=quest_contract,
                warriors=warriors,
                outcome=QUESTS_BY_NAME[quest_contract.quest].draw_outcome(warriors=warriors),
                month=context.month,
            )
        )

    return messages
