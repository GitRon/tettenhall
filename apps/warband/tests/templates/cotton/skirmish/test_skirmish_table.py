from django.urls import reverse

from apps.common.tests.html import parse, render_component
from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.skirmish.models.skirmish import Skirmish
from apps.warband.skirmish.tests.factories.skirmish import SkirmishFactory

OPEN_TABLE_TAG = (
    '<c-skirmish.skirmish-table :skirmish_list="skirmish_list" action_icon="fa-arrow-right"'
    ' action_label="Continue the fight at" empty_text="No fight is holding the month." />'
)
DECIDED_TABLE_TAG = (
    '<c-skirmish.skirmish-table :skirmish_list="skirmish_list" show_victor action_icon="fa-magnifying-glass"'
    ' action_label="Read the report of" empty_text="No skirmishes have been fought yet." />'
)


def _skirmish() -> Skirmish:
    return SkirmishFactory.build(
        id=4,
        name="Battle at the ford",
        attacking_faction=FactionFactory.build(name="Mercia"),
        defending_faction=FactionFactory.build(name="Wessex"),
    )


def test_skirmish_table_names_no_victor_for_an_open_fight():
    html = render_component(tag=OPEN_TABLE_TAG, context={"skirmish_list": [_skirmish()]})

    result = [header.get_text(strip=True) for header in parse(html).find_all("th")]

    assert result == ["Name", "Month", "Attacker", "Defender", "Rounds", ""]


def test_skirmish_table_names_the_victor_of_a_decided_fight():
    html = render_component(tag=DECIDED_TABLE_TAG, context={"skirmish_list": [_skirmish()]})

    result = [header.get_text(strip=True) for header in parse(html).find_all("th")]

    assert result == ["Name", "Month", "Attacker", "Defender", "Rounds", "Victor", ""]


def test_skirmish_table_links_each_fight_by_name():
    html = render_component(tag=OPEN_TABLE_TAG, context={"skirmish_list": [_skirmish()]})

    link = parse(html).find("a")
    result = (link["href"], link["aria-label"])

    assert result == (reverse("warband:skirmish-fight-view", args=[4]), "Continue the fight at Battle at the ford")


def test_skirmish_table_says_so_when_it_is_empty_across_every_column():
    html = render_component(tag=DECIDED_TABLE_TAG, context={"skirmish_list": []})

    cell = parse(html).find("tbody").find("td")
    result = (cell.get_text(strip=True), cell["colspan"])

    assert result == ("No skirmishes have been fought yet.", "7")


def test_skirmish_table_empty_row_spans_the_narrower_table():
    html = render_component(tag=OPEN_TABLE_TAG, context={"skirmish_list": []})

    result = parse(html).find("tbody").find("td")["colspan"]

    assert result == "6"
