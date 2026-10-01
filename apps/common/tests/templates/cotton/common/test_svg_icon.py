from apps.common.tests.html import parse, render_component


def test_svg_icon_named_after_the_icon():
    html = render_component(tag='<c-common.svg-icon icon_name="seax" />', context={})

    result = parse(html).find("span")

    assert result["aria-label"] == "seax"


def test_svg_icon_decorative_hidden_from_assistive_technology():
    html = render_component(tag='<c-common.svg-icon icon_name="silver" decorative />', context={})

    result = parse(html).find("span")

    assert result.get("aria-hidden") == "true"
    assert result.get("aria-label") is None
