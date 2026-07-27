import pytest
from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.management import call_command
from django.test import Client
from queuebie import message_registry
from queuebie.settings import get_queuebie_cache_key

from apps.account.tests.factories.user import UserFactory
from apps.faction.tests.factories.faction import FactionFactory
from apps.savegame.models.savegame import Savegame
from apps.savegame.tests.factories.savegame import SavegameFactory


def _reset_queuebie_registry() -> None:
    """
    Empties the handler registry and drops its cached counterpart.
    """
    cache.delete(get_queuebie_cache_key())
    message_registry.command_dict = {}
    message_registry.event_dict = {}


@pytest.fixture(scope="session")
def django_db_setup(django_db_setup, django_db_blocker):
    """
    Loads the reference data every environment ships with.

    Cultures and item types are lookup tables living in fixtures, not something a test creates:
    the item and warrior generators query them by name, so without them generation raises. Loading
    them once per session keeps tests working against the same reference data as production
    instead of hand-seeding look-alikes.
    """
    with django_db_blocker.unblock():
        call_command("loaddata", "culture", "itemtype")


@pytest.fixture
def user(db) -> User:
    return UserFactory()


@pytest.fixture
def logged_in_client(client, user) -> Client:
    """
    Test client with an authenticated user, since every view sits behind LoginRequiredMiddleware.
    """
    client.force_login(user)

    return client


@pytest.fixture
def current_savegame(user) -> Savegame:
    """
    The active savegame of the logged-in user, including its player faction.

    Several context processors run on every authenticated template render and read
    ``current_savegame.player_faction``, so anything rendering a template needs this complete
    setup rather than a bare savegame.
    """
    savegame = SavegameFactory(created_by=user)
    savegame.player_faction = FactionFactory(savegame=savegame)
    savegame.save()

    return savegame


@pytest.fixture
def savegame_without_player_faction(user) -> Savegame:
    """
    The active savegame of the logged-in user, before its player faction exists.

    A reachable state rather than a contrived one: the savegame row is created first and the faction
    only afterwards. Every view scoped to the player faction has to narrow to nothing here instead
    of dereferencing a missing faction and answering with a 500.
    """
    return SavegameFactory(created_by=user, player_faction=None)


@pytest.fixture
def queuebie_registry():
    """
    Provides a freshly autodiscovered handler registry.

    The registry is a process-wide singleton which is additionally cached in Django's cache backend,
    so without an explicit reset registrations leak between tests.
    """
    _reset_queuebie_registry()
    message_registry.autodiscover()

    yield message_registry

    _reset_queuebie_registry()
