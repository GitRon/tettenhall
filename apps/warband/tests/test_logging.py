import logging

import pytest
from django.conf import settings
from queuebie.runner import handle_message

from apps.warband.skirmish.tests.factories.warrior import WarriorFactory
from apps.warband.warrior.messages.commands.warrior import ReplenishWarriorMorale


@pytest.mark.django_db
def test_bus_debug_lines_reach_a_handler(caplog, queuebie_registry):
    """
    The bus writes a debug line per message it drains. Asserting project-wide once that such a line
    survives is enough - it takes both the configured level and the logger name being the one
    queuebie writes to, and neither is visible in any other test.

    No "caplog.at_level()": forcing the level would set the very thing under test. What reaches the
    capture handler is what the settings let through.
    """
    warrior = WarriorFactory(current_morale=20, max_morale=20)

    handle_message(ReplenishWarriorMorale(warrior=warrior, month=3))

    bus_records = [
        record
        for record in caplog.records
        if record.name == settings.QUEUEBIE_LOGGER_NAME and record.levelno == logging.DEBUG
    ]
    assert len(bus_records) > 0
    assert "handle_replenish_warrior_morale" in bus_records[0].getMessage()
