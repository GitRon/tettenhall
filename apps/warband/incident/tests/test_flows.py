import pytest
from queuebie.runner import handle_message

from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.incident.incidents.hall_relic import HallRelic
from apps.warband.incident.messages.events.incident import IncidentOccurred
from apps.warband.month.models.player_month_log import PlayerMonthLog
from apps.warband.savegame.tests.factories.savegame import SavegameFactory
from apps.warband.skirmish.tests.factories.warrior import WarriorFactory
from apps.warband.warrior.choices.nickname import NicknameStateChoices


@pytest.mark.django_db
def test_a_relic_that_carries_a_man_across_a_threshold_names_him_for_the_relic(queuebie_registry):
    """
    The relic pulls two levers on one man: his ceiling and his name. The ceiling alone would carry him
    to two spreads above his kind's nerve and name him "the Brave", so the order the two awards drain in
    is the whole of what he ends up called. The deed's award is queued beside the ceiling change, the
    threshold's behind the event that change raises - so he is the Believer, and is told so once.

    Dispatched from the event rather than from the month, because which incident a month draws is a
    die, and this is about what happens after it. He is the only man on the roster, so the relic is
    his without patching the draw.
    """
    savegame = SavegameFactory()
    faction = FactionFactory(savegame=savegame, is_player=True)
    # Five short of thirty, which is two spreads above a baseline of twenty: a fifth more crosses it
    warrior = WarriorFactory(faction=faction, savegame=savegame, max_morale=25, nickname_state=None)

    handle_message(IncidentOccurred(faction=faction, month=3, outcome=HallRelic.resolve(faction=faction)))

    warrior.refresh_from_db()
    assert warrior.nickname_state == NicknameStateChoices.RELIC_BEARER
    assert (
        PlayerMonthLog.objects.filter(faction=faction, kind=PlayerMonthLog.KindChoices.KIND_NICKNAME_EARNED).count()
        == 1
    )
