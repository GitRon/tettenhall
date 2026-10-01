import logging
import runpy
import sys
from unittest import mock

import pytest


def test_main_module_runs_the_command_line():
    """
    Run as "python -m" would run it, with "--help" so it answers before touching the database.

    The module silences the bus's info logging for the rest of the process, which in a test run is
    everybody else's too, so it is switched back on here.
    """
    try:
        with mock.patch.object(sys, "argv", ["playtest", "--help"]), pytest.raises(SystemExit, match=r"^0$"):
            runpy.run_module("scripts.playtest", run_name="__main__")
    finally:
        logging.disable(logging.NOTSET)
