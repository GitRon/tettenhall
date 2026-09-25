"""
The pool in "apps/incident/incidents/__init__.py", held to the balance it was weighted for.

These are not arithmetic tests. Each one states an intention about the catalogue as a whole that no
single entry can carry, and reads the constants off the classes - so an entry added or reweighted
without thinking about the drift it causes turns them red.
"""

import pytest

from apps.warband.incident.incidents import INCIDENTS, QUIET_MONTH_WEIGHT
from apps.warband.month.models.player_month_log import PlayerMonthLog


def test_every_entry_carries_a_weight():
    """
    A weight of zero is an entry nobody can ever draw, which is a class kept in the pool by mistake.
    """
    assert [incident for incident in INCIDENTS if incident.WEIGHT <= 0] == []


def test_every_title_fits_the_log_line():
    """
    The title lands in "PlayerMonthLog.title", which is capped, and most titles only reach their full
    length once a name is filled in. Twenty letters is a long name for any culture the game rolls.
    """
    title_length = PlayerMonthLog._meta.get_field("title").max_length
    long_name = "W" * 20

    assert [
        incident
        for incident in INCIDENTS
        if len(incident.TITLE.format(warrior=long_name, rival=long_name, item=long_name)) > title_length
    ] == []


def test_a_quiet_month_is_the_likeliest_outcome():
    """
    The register works because most months are silent. An incident every month is a chronicle
    nobody reads.
    """
    assert sum(incident.WEIGHT for incident in INCIDENTS) < QUIET_MONTH_WEIGHT


def test_silver_nets_out_negative():
    """
    #45 gave insolvency teeth and #3 is about to make silver contested. A pool that pays out on
    average flattens both, so the costs have to outweigh the windfalls.
    """
    weighted_silver = sum(incident.WEIGHT * incident.SILVER_CHANGE for incident in INCIDENTS)

    assert weighted_silver < 0


def test_the_fyrd_nets_out_flat():
    """
    The reserve is the brake on a war band's growth, so a drift here changes the pace of the whole
    game rather than one month of it. "Flat" is a tolerance, not a zero: the entries are whole men.
    """
    weighted_recruits = sum(incident.WEIGHT * incident.FYRD_CHANGE for incident in INCIDENTS)

    assert abs(weighted_recruits) <= 2


def test_the_morale_ceiling_nets_out_flat():
    """
    "max_morale" is close to a one-way ratchet - it otherwise only moves on a level-up - so a drift
    either way accumulates over fifty months with nothing to correct it.
    """
    weighted_share = sum(incident.WEIGHT * incident.MAX_MORALE_SHARE for incident in INCIDENTS)

    # Approximated because the shares are floats: 0.2 three times over is not 0.6
    assert weighted_share == pytest.approx(0)
