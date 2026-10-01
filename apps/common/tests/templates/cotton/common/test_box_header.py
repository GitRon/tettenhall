from apps.common.tests.html import parse, render_component


def test_box_header_shows_what_the_caller_put_inside():
    html = render_component(
        tag="<c-common.box-header>{{ faction.name }}</c-common.box-header>",
        context={"faction": {"name": "Wulfings"}},
    )

    result = parse(html).get_text(strip=True)

    assert result == "Wulfings"
