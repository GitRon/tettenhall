import pytest

from apps.warband.quest.models.quest_contract import QuestContract
from apps.warband.quest.tests.factories.quest_contract import QuestContractFactory


@pytest.mark.django_db
def test_for_player_faction():
    quest_contract = QuestContractFactory()
    QuestContractFactory()

    assert list(QuestContract.objects.for_player_faction(faction_id=quest_contract.faction_id)) == [quest_contract]


@pytest.mark.django_db
def test_accepted_in():
    quest_contract = QuestContractFactory(accepted_in_month=3)
    QuestContractFactory(faction=quest_contract.faction, accepted_in_month=2)

    assert list(QuestContract.objects.accepted_in(month=3)) == [quest_contract]


@pytest.mark.django_db
def test_still_away():
    """Sent before the month and not home yet: this month's men are still out, and a resolved one is home."""
    quest_contract = QuestContractFactory(accepted_in_month=2)
    QuestContractFactory(faction=quest_contract.faction, accepted_in_month=3)
    QuestContractFactory(faction=quest_contract.faction, accepted_in_month=1, resolved_in_month=2)

    assert list(QuestContract.objects.still_away(month=3)) == [quest_contract]


@pytest.mark.django_db
def test_mark_resolved():
    quest_contract = QuestContractFactory(accepted_in_month=2)

    result = QuestContract.objects.mark_resolved(quest_contract=quest_contract, month=3)

    assert result is True
    assert QuestContract.objects.get(pk=quest_contract.pk).resolved_in_month == 3


@pytest.mark.django_db
def test_mark_resolved_twice():
    quest_contract = QuestContractFactory(accepted_in_month=2, resolved_in_month=3)

    result = QuestContract.objects.mark_resolved(quest_contract=quest_contract, month=4)

    assert result is False
    assert QuestContract.objects.get(pk=quest_contract.pk).resolved_in_month == 3
