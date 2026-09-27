import pytest
from django.db import connection


@pytest.mark.django_db
def test_the_suite_opens_its_transactions_immediate():
    """
    A handler's re-read of the purse is only a re-check while nobody else can write between the read
    and the charge, which is what "BEGIN IMMEDIATE" holds - see docs/patterns/message-bus.md. Read off
    the live connection, so the suite is shown to run the mode production runs rather than that a
    settings file mentions it.
    """
    connection.ensure_connection()

    assert connection.transaction_mode == "IMMEDIATE"
