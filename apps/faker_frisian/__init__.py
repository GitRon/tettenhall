"""
Old Frisian names for Faker.

A plain package, deliberately not a Django app: it owns no models and registers through
``Faker.add_provider()`` rather than through Django, so an app config would buy it nothing. It imports
nothing of ours and nothing of Django's - see the import contracts in ``pyproject.toml``.

``data`` documents the orthography every name obeys and says where the pool comes from, ``provider`` the
patterns a place name composes in.
"""

from apps.faker_frisian.data import BYNAMES
from apps.faker_frisian.provider import FRISIAN_BASE_LOCALE, FRISIAN_LOCALE, FrisianProvider
