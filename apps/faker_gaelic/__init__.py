"""
Gaelic names for Faker.

A plain package, deliberately not a Django app: it owns no models and registers through
``Faker.add_provider()`` rather than through Django, so an app config would buy it nothing. It imports
nothing of ours and nothing of Django's - see the import contracts in ``pyproject.toml``.

``data`` documents the orthography every name obeys and carries the inflected forms a place name is
built on, ``provider`` the patterns a place name composes in.
"""

from apps.faker_gaelic.data import BYNAMES
from apps.faker_gaelic.provider import GAELIC_BASE_LOCALE, GAELIC_LOCALE, GaelicProvider
