import pytest

from apps.account.tests.factories.user import UserFactory
from apps.savegame.tests.factories.savegame import SavegameFactory


@pytest.mark.django_db
def test_str_contains_name_and_owner():
    savegame = SavegameFactory(name="First campaign", created_by=UserFactory(first_name="Aethel", last_name="Redwald"))

    assert str(savegame) == "First campaign (Aethel Redwald)"
