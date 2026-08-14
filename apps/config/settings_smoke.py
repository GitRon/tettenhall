"""
Settings used when a browser drives the app for a content review, see the "/implement-story" skill.

Deliberately the application settings, not a stripped-down variant: a content review is only worth
its wall-clock if the app under the browser behaves like the real one. The single change is the
database, pointed at a throwaway file so a smoke run cannot touch the development savegames.
"""

import os
from pathlib import Path

from apps.config.settings import *  # noqa: F403
from apps.config.settings import BASE_DIR

# Every run directory gets its own database, so the path comes from the environment rather than
# being fixed here. The fallback keeps "manage.py ... --settings=apps.config.settings_smoke" usable
# by hand without exporting anything first.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": Path(os.environ.get("SMOKE_DB_PATH", BASE_DIR / "smoke.sqlite3")),
    }
}
