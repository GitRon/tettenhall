import pytest

from apps.faction.tests.factories.faction import FactionFactory
from apps.finance.models import Transaction
from apps.finance.tests.factories.transaction import TransactionFactory
from apps.savegame.tests.factories.savegame import SavegameFactory


@pytest.mark.django_db
def test_for_faction_excludes_the_transactions_of_rival_factions():
    """
    Every faction of a savegame keeps its own purse, so scoping by savegame would hand the player
    the rivals' silver as well.
    """
    savegame = SavegameFactory()
    player_faction = FactionFactory(savegame=savegame)
    rival_faction = FactionFactory(savegame=savegame)
    player_transaction = TransactionFactory(faction=player_faction)
    TransactionFactory(faction=rival_faction)

    result = Transaction.objects.for_faction(faction_id=player_faction.id)

    assert list(result) == [player_transaction]


@pytest.mark.django_db
def test_for_player_faction_excludes_the_transactions_of_rival_factions():
    savegame = SavegameFactory()
    player_faction = FactionFactory(savegame=savegame)
    player_transaction = TransactionFactory(faction=player_faction)
    TransactionFactory(faction=FactionFactory(savegame=savegame))

    result = Transaction.objects.for_player_faction(faction_id=player_faction.id)

    assert list(result) == [player_transaction]


@pytest.mark.django_db
def test_current_balance_sums_up_the_amounts_of_that_faction():
    faction = FactionFactory()
    TransactionFactory(faction=faction, amount=250)
    TransactionFactory(faction=faction, amount=-100)

    assert Transaction.objects.current_balance(faction_id=faction.id) == 150


@pytest.mark.django_db
def test_current_balance_ignores_the_silver_of_a_rival_faction():
    """
    The regression NPC factions would otherwise introduce: rivals earn and spend in the very same
    savegame, so their transactions must not turn up in the player's balance.
    """
    savegame = SavegameFactory()
    player_faction = FactionFactory(savegame=savegame)
    TransactionFactory(faction=player_faction, amount=250)
    TransactionFactory(faction=FactionFactory(savegame=savegame), amount=999)

    assert Transaction.objects.current_balance(faction_id=player_faction.id) == 250


@pytest.mark.django_db
def test_current_balance_without_any_transactions():
    faction = FactionFactory()

    assert Transaction.objects.current_balance(faction_id=faction.id) == 0
