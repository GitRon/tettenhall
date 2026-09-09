"""
Old English names for Faker.

A plain package, deliberately not a Django app: it owns no models and registers through
``Faker.add_provider()`` rather than through Django, so an app config would buy it nothing. It imports
nothing of ours and nothing of Django's - see the import contracts in ``pyproject.toml``.

``data`` documents the orthography every name obeys, ``provider`` the patterns a place name composes
in.
"""

from apps.faker_old_english.data import BYNAMES
from apps.faker_old_english.provider import OLD_ENGLISH_BASE_LOCALE, OLD_ENGLISH_LOCALE, OldEnglishProvider
