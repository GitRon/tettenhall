import pytest
from django.core.cache import cache
from queuebie import message_registry
from queuebie.settings import get_queuebie_cache_key


def _reset_queuebie_registry() -> None:
    """
    Empties the handler registry and drops its cached counterpart.
    """
    cache.delete(get_queuebie_cache_key())
    message_registry.command_dict = {}
    message_registry.event_dict = {}


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
