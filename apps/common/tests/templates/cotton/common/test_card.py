from apps.common.tests.html import parse, render_component


def test_card_shows_each_slot_where_the_caller_put_it():
    html = render_component(
        tag=(
            '<c-common.card><c-slot name="footer">Feast for 40 silver</c-slot>Once a month'
            '<c-slot name="header">{{ title }}</c-slot></c-common.card>'
        ),
        context={"title": "Feast"},
    )

    result = parse(html).get_text(" ", strip=True)

    assert result == "Feast Once a month Feast for 40 silver"


def test_card_carries_its_id_for_an_htmx_target():
    html = render_component(tag='<c-common.card id="fyrd-card">Reserve</c-common.card>', context={})

    result = parse(html).find(id="fyrd-card").get_text(strip=True)

    assert result == "Reserve"
