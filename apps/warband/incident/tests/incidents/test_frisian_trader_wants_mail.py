import pytest

from apps.warband.faction.models.faction import Faction
from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.incident.incidents.base import IncidentQuestion
from apps.warband.incident.incidents.frisian_trader_wants_mail import FrisianTraderWantsMail
from apps.warband.incident.tests.factories.pending_incident import PendingIncidentFactory
from apps.warband.item.models.item_type import ItemType
from apps.warband.item.tests.factories.item import ItemFactory
from apps.warband.item.tests.factories.item_type import ItemTypeFactory
from apps.warband.skirmish.tests.factories.warrior import WarriorFactory


@pytest.fixture
def faction_with_spare_mail() -> Faction:
    faction = FactionFactory()
    armour_type = ItemTypeFactory(name="Chain mail", function=ItemType.FunctionChoices.FUNCTION_ARMOR)
    WarriorFactory(
        faction=faction, armor=ItemFactory(owner=faction, savegame=faction.savegame, type=armour_type, price=200)
    )
    WarriorFactory(
        faction=faction, armor=ItemFactory(owner=faction, savegame=faction.savegame, type=armour_type, price=30)
    )
    return faction


@pytest.mark.django_db
def test_is_possible_with_spare_armour(faction_with_spare_mail):
    assert FrisianTraderWantsMail.is_possible(faction=faction_with_spare_mail) is True


@pytest.mark.django_db
def test_is_possible_with_only_spare_weapons():
    """
    The trader wants something to wear. A spare spear is losable to a moor, not saleable to him.
    """
    faction = FactionFactory()
    WarriorFactory(faction=faction, weapon=ItemFactory(owner=faction, savegame=faction.savegame, price=200))
    WarriorFactory(faction=faction, weapon=ItemFactory(owner=faction, savegame=faction.savegame, price=30))

    assert FrisianTraderWantsMail.is_possible(faction=faction) is False


@pytest.mark.django_db
def test_ask_names_the_spare_piece_and_never_the_finest():
    faction = FactionFactory()
    armour_type = ItemTypeFactory(name="Chain mail", function=ItemType.FunctionChoices.FUNCTION_ARMOR)
    finest_mail = ItemFactory(owner=faction, savegame=faction.savegame, type=armour_type, price=200)
    spare_mail = ItemFactory(owner=faction, savegame=faction.savegame, type=armour_type, price=30)
    WarriorFactory(faction=faction, armor=finest_mail)
    WarriorFactory(faction=faction, armor=spare_mail)

    result = FrisianTraderWantsMail.ask(faction=faction)

    assert result == IncidentQuestion(
        title="A Frisian trader offered good silver for a spare chain mail.",
        body=FrisianTraderWantsMail.BODY,
        item=spare_mail,
    )


@pytest.mark.django_db
def test_answer_sells_the_piece_the_question_named():
    item = ItemFactory(type=ItemTypeFactory(name="Chain mail", function=ItemType.FunctionChoices.FUNCTION_ARMOR))
    pending_incident = PendingIncidentFactory(incident=FrisianTraderWantsMail.__name__, item=item)

    result = FrisianTraderWantsMail.answer(
        option=FrisianTraderWantsMail.get_option(key="sell"), pending_incident=pending_incident
    )

    assert result.title == "The spare chain mail went to a Frisian trader."
    assert result.lost_item == item


@pytest.mark.django_db
def test_answer_once_the_piece_is_gone():
    """
    The piece can be lost or sold while the question waits, and the default's line still has to read.
    """
    pending_incident = PendingIncidentFactory(incident=FrisianTraderWantsMail.__name__, item=None)

    result = FrisianTraderWantsMail.answer(
        option=FrisianTraderWantsMail.get_option(key="keep"), pending_incident=pending_incident
    )

    assert result.title == "The Frisian trader went away without the mail."
