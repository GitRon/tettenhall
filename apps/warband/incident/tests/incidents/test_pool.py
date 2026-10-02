"""
The pool in "apps/incident/incidents/__init__.py", held to the balance it was weighted for.

These are not arithmetic tests. Each one states an intention about the catalogue as a whole that no
single entry can carry, and reads the constants off the classes - so an entry added or reweighted
without thinking about the drift it causes turns them red. The balance is struck over a year, so an
entry is counted at its yearly weight: one drawn in two months counts a sixth of its weight.
"""

import pytest

from apps.warband.calendar.months import YEAR
from apps.warband.incident.incidents import INCIDENTS, QUIET_MONTH_WEIGHT


def test_every_entry_is_drawn_in_some_month():
    """
    An entry tied to months of the year has to name at least one real month, or it is a class kept in
    the pool that nothing can ever draw.
    """
    assert [incident for incident in INCIDENTS if incident.get_yearly_weight() <= 0] == []


def test_every_entry_carries_a_weight():
    """
    A weight of zero is an entry nobody can ever draw, which is a class kept in the pool by mistake.
    """
    assert [incident for incident in INCIDENTS if incident.WEIGHT <= 0] == []


def test_every_question_declares_its_default_among_its_options():
    """
    An unanswered question takes its default when the month ends, so a default naming no option
    would leave the question with nothing to land.
    """
    assert [
        incident for incident in INCIDENTS if incident.is_question() and incident.get_default_option() is None
    ] == []


def test_no_default_costs_silver():
    """
    The default is what a player who cannot afford anything else is left with. One costing silver
    would open a hole he did not dig - the rule every cost in the pool is held to by "is_possible".
    """
    assert [
        incident for incident in INCIDENTS if incident.is_question() and incident.get_default_option().silver_change < 0
    ] == []


def test_no_default_sells_gear():
    """
    A default lands without asking, and gear is the one lever that destroys something the player
    paid for - handing it over is his decision or nobody's.
    """
    assert [
        incident for incident in INCIDENTS if incident.is_question() and incident.get_default_option().sells_item
    ] == []


def test_a_quiet_month_is_the_likeliest_outcome():
    """
    The register works because most months are silent. An incident every month is a chronicle
    nobody reads. Held in the busiest month of the year, since an entry tied to a few months carries
    its whole year's weight in them.
    """
    busiest_month_weight = max(
        sum(incident.WEIGHT for incident in INCIDENTS if incident.is_drawn_in(calendar_month=calendar_month))
        for calendar_month in YEAR
    )

    assert busiest_month_weight < QUIET_MONTH_WEIGHT


def test_silver_nets_out_negative():
    """
    Insolvency has teeth and silver is meant to be contested. A pool that pays out on average
    flattens both, so the costs have to outweigh the windfalls.
    """
    # A question counts at the answer that is not its default - the one it was written to offer.
    # Counting the default instead would price every question as if it were always ignored
    weighted_silver = sum(
        incident.get_yearly_weight()
        * (
            incident.SILVER_CHANGE
            + sum(option.silver_change for option in incident.OPTIONS if option.key != incident.DEFAULT_OPTION)
        )
        for incident in INCIDENTS
    )

    assert weighted_silver < 0


def test_the_fyrd_nets_out_flat():
    """
    The reserve is the brake on a war band's growth, so a drift here changes the pace of the whole
    game rather than one month of it. "Flat" is a tolerance, not a zero: the entries are whole men.
    """
    # A question counts at the answer that is not its default, as the silver does above
    weighted_recruits = sum(
        incident.get_yearly_weight()
        * (
            incident.FYRD_CHANGE
            + sum(option.fyrd_change for option in incident.OPTIONS if option.key != incident.DEFAULT_OPTION)
        )
        for incident in INCIDENTS
    )

    assert abs(weighted_recruits) <= 2


def test_the_morale_ceiling_nets_out_flat():
    """
    "max_morale" is close to a one-way ratchet - it otherwise only moves on a level-up - so a drift
    either way accumulates over fifty months with nothing to correct it.
    """
    weighted_share = sum(incident.get_yearly_weight() * incident.MAX_MORALE_SHARE for incident in INCIDENTS)

    # Approximated because the shares are floats: 0.2 three times over is not 0.6
    assert weighted_share == pytest.approx(0)
