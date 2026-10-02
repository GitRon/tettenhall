from apps.common.tests.html import parse, render_component
from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.skirmish.models import Warrior
from apps.warband.skirmish.tests.factories.warrior import WarriorFactory
from apps.warband.warrior.domain.knowledge import WarriorKnowledge

ROSTER_ROW_TAG = (
    '<c-warrior.roster-row :warrior="warrior" :knowledge="knowledge" :wage="wage" :unpaid_note="unpaid_note">'
    '<button type="button">Actions for him</button>'
    "</c-warrior.roster-row>"
)


def _warrior(*, leads: bool = False) -> Warrior:
    faction = FactionFactory.build(id=1, leader_id=7 if leads else None)

    return WarriorFactory.build(id=7, faction=faction, name="Eadred", nickname_state=None, portrait_face=None)


def _render(*, warrior: Warrior, wage: int = 30, unpaid_note: str | None = None) -> str:
    return render_component(
        tag=ROSTER_ROW_TAG,
        context={
            "warrior": warrior,
            "knowledge": WarriorKnowledge.COMMANDED,
            "wage": wage,
            "unpaid_note": unpaid_note,
        },
    )


def _cell(html: str, *, label: str) -> str:
    return parse(html).find("td", attrs={"data-label": label}).get_text(" ", strip=True)


def test_roster_row_carries_the_menu_it_is_given():
    html = _render(warrior=_warrior())

    result = parse(html).find("button").get_text(strip=True)

    assert result == "Actions for him"


def test_roster_row_names_the_leader_by_his_seat():
    html = _render(warrior=_warrior(leads=True))

    result = "Ealdorman" in parse(html).get_text(" ", strip=True)

    assert result is True


def test_roster_row_gives_no_seat_to_a_man_who_does_not_hold_it():
    html = _render(warrior=_warrior())

    result = "Ealdorman" in parse(html).get_text(" ", strip=True)

    assert result is False


def test_roster_row_says_why_his_morale_is_stuck():
    html = _render(warrior=_warrior(), unpaid_note="Unpaid for 2 months")

    result = "Unpaid for 2 months" in parse(html).get_text(" ", strip=True)

    assert result is True


def test_roster_row_shows_the_wage_it_is_given():
    html = _render(warrior=_warrior(), wage=45)

    result = _cell(html, label="Wage")

    assert result == "45"
