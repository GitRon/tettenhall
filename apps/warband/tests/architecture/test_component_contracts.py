"""
Architectural test for the component call sites in the template layer.

A template component has a contract - the parameters it declares in "<c-vars>" - and cotton enforces
none of it. A tag naming no component raises only when that template renders, an attribute the
component does not declare is swallowed into "attrs", and a required one left out takes whatever the
caller's context holds under that name. Each of those renders a page that looks nearly right, so they
are checked here, over the template sources, for every call site at once.

Every rule is also run against a snippet broken on purpose, so a rule that has stopped seeing anything
fails rather than passing on an empty list.

See docs/patterns/components.md.
"""

from pathlib import Path

from apps.warband.tests.architecture.components import (
    Component,
    call_sites,
    call_sites_in,
    component_files,
    components,
    duplicate_component_names,
    missing_required_attributes,
    undeclared_attributes,
    unknown_components,
)

GAUGE = Component(
    name="warrior.gauge",
    file=Path("gauge.html"),
    required=frozenset({"current", "maximum", "baseline", "knowledge"}),
    defaulted=frozenset({"peak"}),
)


def test_components_are_discovered():
    result = components()

    assert {"common.svg-icon", "common.box-header", "warrior.gauge"} <= result.keys()


def test_call_sites_are_discovered():
    result = {call_site.name for call_site in call_sites()}

    assert {"common.svg-icon", "common.box-header", "warrior.gauge"} <= result


def test_every_call_site_names_a_component():
    result = unknown_components(call_sites=call_sites(), components=components())

    assert result == []


def test_unknown_components_sees_a_misspelt_tag():
    broken = call_sites_in(content='<c-warrior.guage :current="x" />', file_name="broken.html")

    result = unknown_components(call_sites=broken, components={GAUGE.name: GAUGE})

    assert result == ["broken.html:1: <c-warrior.guage>"]


def test_every_passed_attribute_is_declared():
    result = undeclared_attributes(call_sites=call_sites(), components=components())

    assert result == []


def test_undeclared_attributes_sees_a_misspelt_parameter():
    broken = call_sites_in(
        content='<c-warrior.gauge :curent="a" :maximum="b" :baseline="c" :knowledge="d" />',
        file_name="broken.html",
    )

    result = undeclared_attributes(call_sites=broken, components={GAUGE.name: GAUGE})

    assert result == ["broken.html:1: <c-warrior.gauge> passes 'curent'"]


def test_undeclared_attributes_leaves_an_unknown_component_to_its_own_rule():
    broken = call_sites_in(content='<c-warrior.guage :curent="a" />', file_name="broken.html")

    result = undeclared_attributes(call_sites=broken, components={GAUGE.name: GAUGE})

    assert result == []


def test_every_required_attribute_is_passed():
    result = missing_required_attributes(call_sites=call_sites(), components=components())

    assert result == []


def test_missing_required_attributes_sees_a_parameter_left_out():
    broken = call_sites_in(
        content='<c-warrior.gauge :current="a" :maximum="b" :baseline="c" />',
        file_name="broken.html",
    )

    result = missing_required_attributes(call_sites=broken, components={GAUGE.name: GAUGE})

    assert result == ["broken.html:1: <c-warrior.gauge> leaves out 'knowledge'"]


def test_missing_required_attributes_leaves_an_unknown_component_to_its_own_rule():
    broken = call_sites_in(content="<c-warrior.guage />", file_name="broken.html")

    result = missing_required_attributes(call_sites=broken, components={GAUGE.name: GAUGE})

    assert result == []


def test_no_component_name_is_shipped_by_two_apps():
    result = duplicate_component_names(component_files=component_files())

    assert result == []


def test_duplicate_component_names_sees_the_same_component_in_two_apps():
    shipped_twice = [
        ("common.svg-icon", Path("apps/common/templates/cotton/common/svg_icon.html")),
        ("common.svg-icon", Path("apps/warband/templates/cotton/common/svg_icon.html")),
    ]

    result = duplicate_component_names(component_files=shipped_twice)

    assert len(result) == 1
