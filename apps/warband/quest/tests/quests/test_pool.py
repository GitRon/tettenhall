"""
The catalogue as a whole, read off the constants: what every entry has to be for the board to work.
"""

from apps.warband.month.models.player_month_log import PlayerMonthLog
from apps.warband.quest.quests import QUESTS, QUESTS_BY_NAME
from apps.warband.quest.quests.base import Quest, QuestOutcome
from apps.warband.skirmish.models.warrior import Warrior

TITLE_MAX_LENGTH = PlayerMonthLog._meta.get_field("title").max_length


def _pays_something(outcome: QuestOutcome) -> bool:
    return bool(
        outcome.silver_per_man
        or outcome.renown_per_man
        or outcome.item_function is not None
        or outcome.warrior_generator_class is not None
    )


def test_every_entry_carries_a_weight():
    assert [quest.__name__ for quest in QUESTS if quest.WEIGHT <= 0] == []


def test_every_entry_is_indexed_by_its_name():
    assert set(QUESTS_BY_NAME) == {quest.__name__ for quest in QUESTS}


def test_every_entry_takes_a_band_it_can_be_sent():
    assert [quest.__name__ for quest in QUESTS if not 1 <= quest.MIN_MEN <= quest.MAX_MEN] == []


def test_every_entry_leans_on_a_warrior_attribute():
    attribute_names = {field.name for field in Warrior._meta.get_fields()}

    assert [quest.__name__ for quest in QUESTS if quest.LEANS_ON not in attribute_names] == []


def test_every_title_fits_the_log_line():
    titles = [quest.TITLE for quest in QUESTS] + [outcome.title for quest in QUESTS for outcome in quest.OUTCOMES]

    assert [title for title in titles if len(title) > TITLE_MAX_LENGTH] == []


def test_the_lapsed_line_fits_the_log_line():
    assert len(Quest.LAPSED_TITLE) <= TITLE_MAX_LENGTH


def test_every_entry_can_succeed_and_can_fail():
    """
    A quest that can only succeed is a payment, and one that can only fail is a trap. The band's
    attribute only moves the successes, so both sides need a weight for the draw to mean anything.
    """
    one_sided = [
        quest.__name__
        for quest in QUESTS
        if not any(outcome.is_success and outcome.weight > 0 for outcome in quest.OUTCOMES)
        or not any(not outcome.is_success and outcome.weight > 0 for outcome in quest.OUTCOMES)
    ]

    assert one_sided == []


def test_every_success_brings_something_home():
    """
    The expected value of a quest is positive for a band at its yardstick: no lever is ever negative,
    so it is enough that every success pays.
    """
    empty_successes = [
        f"{quest.__name__}.{outcome.key}"
        for quest in QUESTS
        for outcome in quest.OUTCOMES
        if outcome.is_success and not _pays_something(outcome)
    ]

    assert empty_successes == []


def test_every_item_names_its_generator():
    incomplete = [
        f"{quest.__name__}.{outcome.key}"
        for quest in QUESTS
        for outcome in quest.OUTCOMES
        if (outcome.item_function is None) != (outcome.item_generator_class is None)
    ]

    assert incomplete == []


def test_every_odd_job_pays_silver_on_every_outcome():
    """The errand that is always on offer is the one a war band short of silver can count on."""
    unpaid = [
        f"{quest.__name__}.{outcome.key}"
        for quest in QUESTS
        if quest.IS_ODD_JOB
        for outcome in quest.OUTCOMES
        if outcome.silver_per_man <= 0
    ]

    assert unpaid == []


def test_the_catalogue_has_an_odd_job_and_an_errand():
    assert {quest.IS_ODD_JOB for quest in QUESTS} == {True, False}
