from apps.common.tests.html import parse, render_component
from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.savegame.tests.factories.savegame import SavegameFactory
from apps.warband.skirmish.tests.factories.warrior import WarriorFactory
from apps.warband.warrior.choices.modified_attribute import ModifiedAttributeChoices
from apps.warband.warrior.models.injury import Injury
from apps.warband.warrior.tests.factories.injury import InjuryFactory
from apps.warband.warrior.tests.factories.injury_type import InjuryTypeFactory

INJURY_ROW_TAG = '<c-warrior.injury-row :injuries="injuries" />'


def _injury(*, name: str, attribute: str, magnitude: int = 1, month: int = 1) -> Injury:
    warrior = WarriorFactory.build(faction=FactionFactory.build(savegame=SavegameFactory.build(start_year=768)))

    return InjuryFactory.build(
        warrior=warrior,
        type=InjuryTypeFactory.build(name=name, attribute=attribute, magnitude=magnitude),
        inflicted_in_month=month,
    )


def _lines(html: str) -> list[str]:
    """Each injury as a player reads it: the template wraps the line, and the newlines reach the text."""
    return [" ".join(item.get_text(" ").split()) for item in parse(html).find_all("li")]


def test_injury_row_is_silent_for_a_whole_man():
    html = render_component(tag=INJURY_ROW_TAG, context={"injuries": []})

    result = parse(html).get_text(strip=True)

    assert result == ""


def test_injury_row_names_the_mark_what_it_costs_and_when_he_took_it():
    injury = _injury(name="Stiff ankle", attribute=ModifiedAttributeChoices.ATTRIBUTE_DEXTERITY, month=3)

    html = render_component(tag=INJURY_ROW_TAG, context={"injuries": [injury]})

    result = _lines(html)

    assert result == ["Stiff ankle (-1 Dexterity) since Ærra Liða · Summer · AD 768"]


def test_injury_row_lists_every_mark_on_the_same_attribute_and_on_another():
    """Two marks on one attribute are two lines, not a sum: each is a thing that happened to him."""
    injuries = [
        _injury(name="Missing finger", attribute=ModifiedAttributeChoices.ATTRIBUTE_STRENGTH, month=1),
        _injury(name="Cracked ribs", attribute=ModifiedAttributeChoices.ATTRIBUTE_STRENGTH, month=3),
        _injury(name="Stiff ankle", attribute=ModifiedAttributeChoices.ATTRIBUTE_DEXTERITY, month=10),
    ]

    html = render_component(tag=INJURY_ROW_TAG, context={"injuries": injuries})

    result = _lines(html)

    assert result == [
        "Missing finger (-1 Strength) since Eosturmonath · Summer · AD 768",
        "Cracked ribs (-1 Strength) since Ærra Liða · Summer · AD 768",
        "Stiff ankle (-1 Dexterity) since Æfterra Geola · Winter · AD 769",
    ]
