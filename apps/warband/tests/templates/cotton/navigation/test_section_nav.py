from apps.common.tests.html import parse, render_component

SECTION_NAV_TAG = '<c-navigation.section-nav :sections="sections" :current="current" />'

SECTIONS = [
    {"key": "month", "label": "Month", "icon": "fa-calendar", "url": "/account/dashboard/"},
    {"key": "warband", "label": "War band", "icon": "fa-users", "url": "/faction/warband/roster"},
]


def test_section_nav_renders_nothing_without_sections():
    html = render_component(tag=SECTION_NAV_TAG, context={"sections": [], "current": None})

    result = parse(html).find("nav")

    assert result is None


def test_section_nav_links_every_section():
    html = render_component(tag=SECTION_NAV_TAG, context={"sections": SECTIONS, "current": "month"})

    result = [(link.get_text(strip=True), link["href"]) for link in parse(html).find_all("a")]

    assert result == [("Month", "/account/dashboard/"), ("War band", "/faction/warband/roster")]


def test_section_nav_marks_only_the_current_section():
    html = render_component(tag=SECTION_NAV_TAG, context={"sections": SECTIONS, "current": "warband"})

    result = [link.get_text(strip=True) for link in parse(html).find_all("a", attrs={"aria-current": "page"})]

    assert result == ["War band"]


def test_section_nav_marks_nothing_without_a_current_section():
    html = render_component(
        tag='<c-navigation.section-nav :sections="sections" />',
        context={"sections": SECTIONS},
    )

    result = parse(html).find_all("a", attrs={"aria-current": True})

    assert result == []
