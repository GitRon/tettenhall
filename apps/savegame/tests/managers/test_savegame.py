import pytest

from apps.account.tests.factories.user import UserFactory
from apps.savegame.models.savegame import Savegame
from apps.savegame.tests.factories.savegame import SavegameFactory


@pytest.mark.django_db
def test_set_all_others_from_user_to_inactive_deactivates_the_other_savegames_of_the_user():
    user = UserFactory()
    savegame = SavegameFactory(created_by=user)
    other_savegame = SavegameFactory(created_by=user, is_active=True)

    Savegame.objects.set_all_others_from_user_to_inactive(savegame_id=savegame.id, user_id=user.id)

    other_savegame.refresh_from_db()
    assert other_savegame.is_active is False


@pytest.mark.django_db
def test_set_all_others_from_user_to_inactive_keeps_savegames_of_other_users_active():
    savegame = SavegameFactory()
    savegame_of_other_user = SavegameFactory(created_by=UserFactory())

    Savegame.objects.set_all_others_from_user_to_inactive(savegame_id=savegame.id, user_id=savegame.created_by_id)

    savegame_of_other_user.refresh_from_db()
    assert savegame_of_other_user.is_active is True
