import pytest

from apps.faction.tests.factories.faction import FactionFactory
from apps.finance.handlers.events.quest_contract import handle_victorious_faction_gets_quest_reward
from apps.finance.messages.commands.transaction import CreateTransaction
from apps.skirmish.messages.events.skirmish import SkirmishFinished
from apps.skirmish.tests.factories.skirmish import SkirmishFactory


@pytest.mark.django_db
def test_handle_victorious_faction_gets_quest_reward_creates_transaction_for_loot():
    victorious_faction = FactionFactory()
    skirmish = SkirmishFactory(victorious_faction=victorious_faction)
    context = SkirmishFinished(
        skirmish=skirmish,
        incapacitated_warriors=[],
        defeated_unconscious_warriors=[],
        victorious_healthy_warriors=[],
        quest_name="Rescue the ealdorman",
        quest_loot=250,
        month=4,
    )

    result = handle_victorious_faction_gets_quest_reward(context=context)

    assert result == CreateTransaction(
        faction=victorious_faction,
        amount=250,
        reason="Quest 'Rescue the ealdorman' finished! 250 silver looted.",
        month=4,
    )


@pytest.mark.django_db
def test_handle_victorious_faction_gets_quest_reward_without_loot():
    skirmish = SkirmishFactory(victorious_faction=FactionFactory())
    context = SkirmishFinished(
        skirmish=skirmish,
        incapacitated_warriors=[],
        defeated_unconscious_warriors=[],
        victorious_healthy_warriors=[],
        quest_name="Rescue the ealdorman",
        quest_loot=0,
        month=4,
    )

    result = handle_victorious_faction_gets_quest_reward(context=context)

    assert result is None
