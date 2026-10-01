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
from apps.warband.skirmish.models import Warrior
from apps.warband.skirmish.projections.payroll import Payroll
from apps.warband.skirmish.tests.factories.warrior import WarriorFactory
from apps.warband.tests.architecture.components import components
from apps.warband.warrior.domain.knowledge import WarriorKnowledge


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
        leader_id=1,
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
    "finance.wage-bill-warning": [
        ('<c-finance.wage-bill-warning :payroll="payroll" />', {"payroll": _payroll(budget=0)}),
        (
            '<c-finance.wage-bill-warning :payroll="payroll" show_finance_link />',
            {"payroll": _payroll(budget=0, unpaid_months=Warrior.UNPAID_MONTHS_UNTIL_WALKOUT)},
        ),
    ],
    "navigation.section-nav": [
        ('<c-navigation.section-nav :sections="sections" />', {"sections": NAV_SECTIONS}),
        (
            '<c-navigation.section-nav :sections="sections" :current="current" />',
            {"sections": NAV_SECTIONS, "current": "month"},
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
