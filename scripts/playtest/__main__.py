"""
Entry point: "python -m scripts.playtest --output report.json".

Runs on the smoke settings unless DJANGO_SETTINGS_MODULE says otherwise, so a run lands in a throwaway
database rather than among the development savegames.
"""

import logging
import os
import sys

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "apps.config.settings_smoke")
django.setup()
# The bus logs every message it handles, which for a few hundred savegames buries the one line per game
logging.disable(logging.INFO)

# Only importable once Django is set up, because it reaches the models
from scripts.playtest.cli import main  # noqa: E402

sys.exit(main(argv=sys.argv[1:]))
