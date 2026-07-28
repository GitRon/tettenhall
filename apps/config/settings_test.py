"""
Settings used when running the test suite.
"""

from apps.config.settings import *  # noqa: F403

# Tests don't need a secure (and therefore slow) hasher
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# Keep strict mode enabled: it rejects commands being registered across app borders and blocks
# database access inside event handlers when they run through "handle_message()".
QUEUEBIE_STRICT_MODE = True

# Dedicated local-memory cache so the cached queuebie handler registry can be reset between tests.
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "tettenhall-tests",
    }
}
