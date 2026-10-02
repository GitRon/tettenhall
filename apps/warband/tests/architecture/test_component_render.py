"""
Every component renders, once with only what it requires and once with everything, plus one row per
branch it takes on its data.

The test asserts nothing about the output. It fails when a render raises, or when a variable the
component reads does not resolve - "string_if_invalid" is set to a value that raises instead of
printing nothing, because nothing is exactly how a renamed parameter looks on the page.

A component without an entry below fails "test_every_component_has_render_rows", so a new component
cannot ship without being rendered here.

It is also what notices a Django upgrade breaking cotton: the library patches Django's template lexer,
which is private API - see apps/config/settings.py.

See docs/patterns/components.md.
"""

import copy

import pytest
from django.conf import settings
from django.test import override_settings

from apps.common.tests.html import render_component
from apps.warband.calendar.months.summer import Eosturmonath
from apps.warband.calendar.months.winter import Blotmonath
from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.incident.incidents.base import IncidentOption
from apps.warband.incident.services.pending_incident import OpenQuestion
from apps.warband.incident.tests.factories.pending_incident import PendingIncidentFactory
from apps.warband.item.models.item_type import ItemType
from apps.warband.item.tests.factories.item import ItemFactory
from apps.warband.item.tests.factories.item_type import ItemTypeFactory
from apps.warband.month.services.player_month_log import GroupedPlayerMonthLog
from apps.warband.month.tests.factories.player_month_log import PlayerMonthLogFactory
from apps.warband.skirmish.models import Warrior
from apps.warband.skirmish.models.battle_history import BattleHistory
from apps.warband.skirmish.models.skirmish import Skirmish
from apps.warband.skirmish.projections.payroll import Payroll
from apps.warband.skirmish.tests.factories.skirmish import SkirmishFactory
from apps.warband.skirmish.tests.factories.warrior import WarriorFactory
from apps.warband.tests.architecture.components import components
from apps.warband.warrior.domain.knowledge import WarriorKnowledge
from apps.warband.warrior.models.hair_colour import HairColour
from apps.warband.warrior.models.portrait_piece import PortraitPiece


class RaisingInvalidString(str):
    """
    Django prints "string_if_invalid % variable name" when it contains "%s", so claiming to contain it
    and raising on the formatting turns every unresolved variable into an error.
    """

    def __contains__(self, key: str) -> bool:
        return key == "%s"

    def __mod__(self, variable_name: object) -> str:
        raise AssertionError(f"Template variable '{variable_name}' does not resolve")


def _raising_templates() -> list[dict]:
    templates = copy.deepcopy(settings.TEMPLATES)
    templates[0]["OPTIONS"]["string_if_invalid"] = RaisingInvalidString("unresolved")

    return templates


def _payroll(*, budget: int, unpaid_months: int = 0) -> Payroll:
    return Payroll(
        warrior_list=[
            WarriorFactory.build(id=1, monthly_salary=30),
            WarriorFactory.build(id=2, monthly_salary=40, unpaid_months=unpaid_months),
        ],
        budget=budget,
    )


def _full_month() -> GroupedPlayerMonthLog:
    return GroupedPlayerMonthLog(
        attention=[PlayerMonthLogFactory.build(title="Unpaid")],
        chronicle=[PlayerMonthLogFactory.build(title="A comet", body="Over Mercia")],
        consequence=[PlayerMonthLogFactory.build(title="Wages paid")],
        upkeep=[PlayerMonthLogFactory.build(title="Wulfstan mends")],
        upkeep_summary=["1 man mends"],
    )


def _open_question() -> OpenQuestion:
    return OpenQuestion(
        pending_incident=PendingIncidentFactory.build(id=1),
        options=(IncidentOption(key="give", label="Give", title="", body="", silver_change=-60, fyrd_change=1),),
    )


def _built_skirmish() -> Skirmish:
    return SkirmishFactory.build(
        id=1, attacking_faction=FactionFactory.build(id=1), defending_faction=FactionFactory.build(id=2)
    )


def _drawn_warrior() -> Warrior:
    return WarriorFactory.build(
        id=1,
        portrait_face=PortraitPiece(image="img/warrior/portrait/face/01.png"),
        portrait_beard=PortraitPiece(image="img/warrior/portrait/beard/01.png"),
        portrait_hair=PortraitPiece(image="img/warrior/portrait/hair/01.png"),
        beard_colour=HairColour(hex="#6b3a1f"),
        hair_colour=HairColour(hex="#2a1a10"),
    )


NAV_SECTIONS = [{"key": "month", "label": "Month", "icon": "fa-calendar", "url": "/account/dashboard/"}]


RENDER_ROWS = {
    "common.svg-icon": [
        ('<c-common.svg-icon icon_name="seax" />', {}),
        ('<c-common.svg-icon icon_name="seax" size="xl" decorative />', {}),
    ],
    "common.box-header": [
        ("<c-common.box-header>Battle report</c-common.box-header>", {}),
    ],
    "common.card": [
        ("<c-common.card>Current costs</c-common.card>", {}),
        (
            '<c-common.card id="fyrd-card" class="mb-5"><c-slot name="header">Feast</c-slot>'
            'Once a month<c-slot name="footer">Feast for 40 silver</c-slot></c-common.card>',
            {},
        ),
        (
            '<c-common.card><c-slot name="header">Seax</c-slot> <c-slot name="footer">Buy</c-slot></c-common.card>',
            {},
        ),
    ],
    "calendar.month-effects": [
        ('<c-calendar.month-effects :calendar_month="calendar_month" />', {"calendar_month": Eosturmonath}),
        (
            '<c-calendar.month-effects heading="Next" :calendar_month="calendar_month" />',
            {"calendar_month": Blotmonath},
        ),
    ],
    "calendar.march-cost-row": [
        ('<c-calendar.march-cost-row :calendar_month="calendar_month" />', {"calendar_month": Eosturmonath}),
        ('<c-calendar.march-cost-row :calendar_month="calendar_month" />', {"calendar_month": Blotmonath}),
    ],
    "faction.successor-line": [
        (
            '<c-faction.successor-line :leader="leader" :successor="successor" />',
            {"leader": WarriorFactory.build(), "successor": None},
        ),
        (
            '<c-faction.successor-line :leader="leader" :successor="successor" />',
            {"leader": WarriorFactory.build(), "successor": WarriorFactory.build()},
        ),
    ],
    "finance.wage-bill-warning": [
        ('<c-finance.wage-bill-warning :payroll="payroll" />', {"payroll": _payroll(budget=0)}),
        (
            '<c-finance.wage-bill-warning :payroll="payroll" show_finance_link />',
            {"payroll": _payroll(budget=0, unpaid_months=Warrior.UNPAID_MONTHS_UNTIL_WALKOUT)},
        ),
    ],
    "item.improves-nobody-tag": [
        ("<c-item.improves-nobody-tag />", {}),
    ],
    "item.stats-meta": [
        ('<c-item.stats-meta :item="item" />', {"item": ItemFactory.build(type=ItemTypeFactory.build())}),
        ('<c-item.stats-meta :item="item" show_price />', {"item": ItemFactory.build(type=ItemTypeFactory.build())}),
    ],
    "month.log-list": [
        ('<c-month.log-list :logs="logs" />', {"logs": GroupedPlayerMonthLog()}),
        (
            '<c-month.log-list :logs="logs" :questions="questions" />',
            {"logs": _full_month(), "questions": [_open_question()]},
        ),
    ],
    "month.log-brief": [
        (
            '<c-month.log-brief :logs="logs" />',
            {"logs": GroupedPlayerMonthLog(consequence=[PlayerMonthLogFactory.build(title="Wages paid")])},
        ),
        ('<c-month.log-brief :logs="logs" />', {"logs": _full_month()}),
    ],
    "navigation.section-nav": [
        ('<c-navigation.section-nav :sections="sections" />', {"sections": NAV_SECTIONS}),
        (
            '<c-navigation.section-nav :sections="sections" :current="current" />',
            {"sections": NAV_SECTIONS, "current": "month"},
        ),
    ],
    "skirmish.log-line": [
        (
            '<c-skirmish.log-line :log="log" :text="text" />',
            {"log": BattleHistory(kind=BattleHistory.KindChoices.KIND_NARRATION, faction_id=1), "text": "A swing"},
        ),
        (
            '<c-skirmish.log-line :log="log" :text="text" :player_faction_id="player_faction_id" />',
            {
                "log": BattleHistory(kind=BattleHistory.KindChoices.KIND_WARRIOR_KILLED, faction_id=1),
                "text": "He falls",
                "player_faction_id": 1,
            },
        ),
    ],
    "skirmish.faction-box": [
        (
            '<c-skirmish.faction-box :faction="faction" :warrior_list="warrior_list" :is_player="is_player"'
            ' :skirmish="skirmish" :skirmish_is_decided="skirmish_is_decided" />',
            {
                "faction": FactionFactory.build(id=1),
                "warrior_list": [],
                "is_player": True,
                "skirmish": _built_skirmish(),
                "skirmish_is_decided": False,
            },
        ),
    ],
    "skirmish.skirmish-table": [
        (
            '<c-skirmish.skirmish-table :skirmish_list="skirmish_list" action_icon="fa-arrow-right"'
            ' action_label="Continue the fight at" empty_text="Nothing" />',
            {"skirmish_list": []},
        ),
        (
            '<c-skirmish.skirmish-table :skirmish_list="skirmish_list" show_victor action_icon="fa-magnifying-glass"'
            ' action_label="Read the report of" empty_text="Nothing" />',
            {"skirmish_list": [_built_skirmish()]},
        ),
    ],
    "warrior.attribute": [
        (
            '<c-warrior.attribute :value="value" :baseline="baseline" :knowledge="knowledge" />',
            {"value": 12, "baseline": 10, "knowledge": WarriorKnowledge.COMMANDED},
        ),
        (
            '<c-warrior.attribute :value="value" :baseline="baseline" :knowledge="knowledge" />',
            {"value": 12, "baseline": 10, "knowledge": WarriorKnowledge.RIVAL},
        ),
    ],
    "warrior.portrait": [
        ('<c-warrior.portrait :warrior="warrior" />', {"warrior": WarriorFactory.build(portrait_face=None)}),
        ('<c-warrior.portrait :warrior="warrior" crop="full" frame="border" />', {"warrior": _drawn_warrior()}),
    ],
    "warrior.portrait-layer": [
        (
            '<c-warrior.portrait-layer :piece="piece" />',
            {"piece": PortraitPiece(image="img/warrior/portrait/hair/01.png")},
        ),
        (
            '<c-warrior.portrait-layer :piece="piece" :colour="colour" />',
            {"piece": PortraitPiece(image="img/warrior/portrait/hair/01.png"), "colour": HairColour(hex="#2a1a10")},
        ),
    ],
    "warrior.row": [
        (
            '<c-warrior.row :warrior="warrior" :knowledge="knowledge" />',
            {"warrior": WarriorFactory.build(id=1), "knowledge": WarriorKnowledge.RIVAL},
        ),
        (
            '<c-warrior.row :warrior="warrior" :knowledge="knowledge" is_pub :is_player_faction="is_player_faction" />',
            {
                "warrior": WarriorFactory.build(
                    id=1,
                    pub_arrival_month=1,
                    monthly_salary=20,
                    weapon=ItemFactory.build(type=ItemTypeFactory.build()),
                    armor=ItemFactory.build(type=ItemTypeFactory.build()),
                ),
                "knowledge": WarriorKnowledge.COMMANDED,
                "is_player_faction": True,
            },
        ),
    ],
    "warrior.roster-gauge": [
        (
            '<c-warrior.roster-gauge :current="current" :maximum="maximum" :baseline="baseline"'
            ' :knowledge="knowledge" />',
            {"current": 1, "maximum": 5, "baseline": 4, "knowledge": WarriorKnowledge.COMMANDED},
        ),
        (
            '<c-warrior.roster-gauge :current="current" :maximum="maximum" :peak="peak" :baseline="baseline"'
            ' :knowledge="knowledge" />',
            {"current": 4, "maximum": 5, "peak": 9, "baseline": 4, "knowledge": WarriorKnowledge.COMMANDED},
        ),
        (
            '<c-warrior.roster-gauge :current="current" :maximum="maximum" :baseline="baseline"'
            ' :knowledge="knowledge" />',
            {"current": 3, "maximum": 5, "baseline": 4, "knowledge": WarriorKnowledge.HELD},
        ),
    ],
    "warrior.roster-gear": [
        ('<c-warrior.roster-gear :item="item" />', {"item": None}),
        ('<c-warrior.roster-gear :item="item" />', {"item": ItemFactory.build(type=ItemTypeFactory.build())}),
        (
            '<c-warrior.roster-gear :item="item" />',
            {"item": ItemFactory.build(type=ItemTypeFactory.build(function=ItemType.FunctionChoices.FUNCTION_ARMOR))},
        ),
    ],
    "warrior.gauge": [
        (
            '<c-warrior.gauge :current="current" :maximum="maximum" :baseline="baseline" :knowledge="knowledge" />',
            {"current": 3, "maximum": 5, "baseline": 4, "knowledge": WarriorKnowledge.COMMANDED},
        ),
        (
            '<c-warrior.gauge :current="current" :maximum="maximum" :peak="peak" :baseline="baseline"'
            ' :knowledge="knowledge" />',
            {"current": 3, "maximum": 5, "peak": 9, "baseline": 4, "knowledge": WarriorKnowledge.COMMANDED},
        ),
        (
            '<c-warrior.gauge :current="current" :maximum="maximum" :baseline="baseline" :knowledge="knowledge" />',
            {"current": 3, "maximum": 5, "baseline": 4, "knowledge": WarriorKnowledge.RIVAL},
        ),
    ],
}


def test_every_component_has_render_rows():
    result = set(RENDER_ROWS)

    assert result == set(components())


@pytest.mark.parametrize(
    ("tag", "context"),
    [row for rows in RENDER_ROWS.values() for row in rows],
)
def test_component_renders(tag, context):
    with override_settings(TEMPLATES=_raising_templates()):
        result = render_component(tag=tag, context=context)

    assert result.strip() != ""


def test_raising_invalid_string_sees_an_unresolved_variable():
    with (
        override_settings(TEMPLATES=_raising_templates()),
        pytest.raises(AssertionError, match="'maximum' does not resolve"),
    ):
        render_component(
            tag='<c-warrior.gauge :current="current" :knowledge="knowledge" />',
            context={"current": 3, "knowledge": WarriorKnowledge.COMMANDED},
        )
