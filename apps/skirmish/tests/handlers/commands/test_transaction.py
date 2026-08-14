from unittest import mock

import pytest

from apps.skirmish.handlers.commands.transaction import handle_warrior_drops_silver
from apps.skirmish.messages.commands.transaction import WarriorDropsSilver
from apps.skirmish.messages.events.transaction import WarriorDroppedSilver
from apps.skirmish.tests.factories.skirmish import SkirmishFactory
from apps.skirmish.tests.factories.warrior import WarriorFactory


@pytest.mark.django_db
def test_handle_warrior_drops_silver_hands_the_rolled_amount_to_the_victor():
    skirmish = SkirmishFactory()
    warrior = WarriorFactory(faction=skirmish.defending_faction)

    # Boundary randomness: the dropped amount is a gauss roll
    with mock.patch("apps.skirmish.handlers.commands.transaction.random.gauss", return_value=12.4):
        result = handle_warrior_drops_silver(
            context=WarriorDropsSilver(
                skirmish=skirmish, warrior=warrior, gaining_faction=skirmish.attacking_faction, month=3
            )
        )

    assert result == [
        WarriorDroppedSilver(
            skirmish=skirmish,
            warrior=warrior,
            gaining_faction=skirmish.attacking_faction,
            amount=12,
            month=3,
        )
    ]


@pytest.mark.django_db
def test_handle_warrior_drops_silver_drops_nothing_on_a_zero_roll():
    skirmish = SkirmishFactory()
    warrior = WarriorFactory(faction=skirmish.defending_faction)

    # Boundary randomness: a negative roll is clamped to zero, which means no silver at all
    with mock.patch("apps.skirmish.handlers.commands.transaction.random.gauss", return_value=-3.0):
        result = handle_warrior_drops_silver(
            context=WarriorDropsSilver(
                skirmish=skirmish, warrior=warrior, gaining_faction=skirmish.attacking_faction, month=3
            )
        )

    assert result == []
