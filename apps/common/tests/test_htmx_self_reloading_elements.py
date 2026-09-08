"""
Architectural test for the self-reloading htmx elements in the template layer.

An element carrying both "hx-get" and a "from:body" trigger re-fetches itself whenever some other
view fires that event. htmx's default swap is "innerHTML", so if the response contains the listening
element itself - which it does whenever the view renders the very template the element lives in - the
reloaded copy lands *inside* the original and the page now holds two listeners for the same event.
The next event fires both, giving four, then eight: the cost of a click grows geometrically with the
clicks before it on the same page load.

Nothing shows wrong data, because the last swap wins and it is correct, so no test asserting status
or context can see this and no player will report it. What the defect is, is a missing attribute -
which is why it is checked here, over the template sources, for every such element at once.

The second check is the other half of the same decision. "hx-swap" is an inherited attribute, so a
wrapper that sets "outerHTML" for itself also sets it for every control inside it - and a control
written against the default swap then replaces its own target instead of filling it. "hx-disinherit"
is what keeps the wrapper's choice to the wrapper.
"""

import re
from pathlib import Path

from django.conf import settings

# A Django tag or comment can carry a ">" ("{% if a > b %}"), which would end an element early for
# the scan below. Blanking them first keeps the offsets - and so the reported line numbers - intact.
DJANGO_TAG_PATTERN = re.compile(r"{%.*?%}|{#.*?#}", re.DOTALL)

OPENING_ELEMENT_PATTERN = re.compile(r"<[a-zA-Z][^<>]*>")

SELF_RELOADING_TRIGGER_PATTERN = re.compile(r'hx-trigger="[^"]*from:body')

# "hx-swap-oob" is a different attribute - an out-of-band swap declared by a *response* - and says
# nothing about how this element swaps. Matching it as "hx-swap" would pass an element that never
# made the decision.
SWAP_ATTRIBUTE_PATTERN = re.compile(r"hx-swap=")

OUTER_HTML_SWAP_PATTERN = re.compile(r'hx-swap="outerHTML"')

DISINHERIT_SWAP_PATTERN = re.compile(r'hx-disinherit="[^"]*hx-swap')


def _template_files() -> list[Path]:
    # Every app ships its templates under its own "templates/" directory - "DIRS" is empty and
    # "APP_DIRS" is on, so there is no second place for one to hide
    return sorted((Path(settings.BASE_DIR) / "apps").glob("**/templates/**/*.html"))


def _blank_django_tags(*, content: str) -> str:
    return DJANGO_TAG_PATTERN.sub(lambda match: re.sub(r"[^\n]", " ", match.group()), content)


def _self_reloading_elements(*, file: Path) -> list[tuple[str, str]]:
    """
    Every element that re-fetches itself on a body event, as (location, the opening tag).
    """
    content = _blank_django_tags(content=file.read_text(encoding="utf-8"))
    elements = []

    for match in OPENING_ELEMENT_PATTERN.finditer(content):
        element = match.group()

        if "hx-get" not in element or not SELF_RELOADING_TRIGGER_PATTERN.search(element):
            continue

        elements.append((f"{file.name}:{content.count('\n', 0, match.start()) + 1}", element))

    return elements


def _all_self_reloading_elements() -> list[tuple[str, str]]:
    return [element for file in _template_files() for element in _self_reloading_elements(file=file)]


def test_self_reloading_elements_declare_how_they_are_swapped():
    """
    Declaring "hx-swap" is what keeps the response from nesting a second listener inside the first.

    "outerHTML" for an element whose view renders the element itself, which is the common shape here;
    "innerHTML" together with an "hx-target" for one that only wraps a separate inner partial. Either
    is a decision; the default is not.
    """
    violations = [
        location for location, element in _all_self_reloading_elements() if not SWAP_ATTRIBUTE_PATTERN.search(element)
    ]

    assert violations == []


def test_elements_swapping_themselves_out_do_not_impose_that_on_their_contents():
    """
    An "outerHTML" wrapper holding a control that says nothing about its own swap would make that
    control replace its target rather than fill it - and on the second click the target is gone, so
    htmx raises "targetError" and the click does nothing at all.
    """
    violations = [
        location
        for location, element in _all_self_reloading_elements()
        if OUTER_HTML_SWAP_PATTERN.search(element) and not DISINHERIT_SWAP_PATTERN.search(element)
    ]

    assert violations == []
