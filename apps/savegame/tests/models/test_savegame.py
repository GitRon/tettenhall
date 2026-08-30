import pytest

from apps.account.tests.factories.user import UserFactory
from apps.faction.models.faction import Faction
from apps.faction.tests.factories.faction import FactionFactory
from apps.month.tests.factories.player_month_log import PlayerMonthLogFactory
from apps.savegame.models.savegame import Savegame
from apps.savegame.tests.factories.savegame import SavegameFactory
from apps.skirmish.tests.factories.warrior import WarriorFactory


@pytest.mark.django_db
def test_str_contains_name_and_owner():
    savegame = SavegameFactory(name="First campaign", created_by=UserFactory(first_name="Aethel", last_name="Redwald"))

    assert str(savegame) == "First campaign (Aethel Redwald)"


@pytest.mark.django_db
def test_a_savegame_deletes_together_with_everything_hanging_off_it():
    """
    Every model in the game hangs off "Savegame", and "Savegame.player_faction" points at a faction
    carrying a foreign key back, so the cascade has a cycle in it. Deleting a savegame by hand is how
    test data gets cleared out, and the two-way link only exists once a game has been started - which
    no factory sets up on its own.
    """
    savegame = SavegameFactory()
    player_faction = FactionFactory(savegame=savegame)
    savegame.player_faction = player_faction
    savegame.save()
    FactionFactory(savegame=savegame)
    WarriorFactory(faction=player_faction, savegame=savegame)
    PlayerMonthLogFactory(faction=player_faction)

    savegame.delete()

    assert Savegame.objects.count() == 0
    assert Faction.objects.count() == 0
