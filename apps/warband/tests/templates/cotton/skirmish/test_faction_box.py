from django.urls import reverse

from apps.common.tests.html import parse, render_component
from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.skirmish.tests.factories.skirmish import SkirmishFactory

FACTION_BOX_TAG = (
    '<c-skirmish.faction-box :faction="faction" :warrior_list="warrior_list" :is_player="is_player"'
    ' :skirmish="skirmish" :skirmish_is_decided="skirmish_is_decided" />'
)


def test_faction_box_refreshes_its_own_side_of_this_fight():
    faction = FactionFactory.build(id=3, name="Mercia")
    skirmish = SkirmishFactory.build(id=9, attacking_faction=faction, defending_faction=FactionFactory.build(id=5))

    html = render_component(
        tag=FACTION_BOX_TAG,
        context={
            "faction": faction,
            "warrior_list": [],
            "is_player": True,
            "skirmish": skirmish,
            "skirmish_is_decided": False,
        },
    )

    result = parse(html).find(attrs={"hx-get": True})["hx-get"]

    assert result == reverse("warband:faction-warrior-list-update-htmx", args=[9, 3])
