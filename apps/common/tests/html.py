"""
Rendering a component on its own and reading what it says.

For component output tests only - see docs/patterns/testing-strategy.md, "Components". A view test never
reads the body.
"""

from bs4 import BeautifulSoup
from django.template import engines
from django_cotton.compiler_regex import CottonCompiler


def render_component(*, tag: str, context: dict) -> str:
    """
    Renders one component call, e.g. '<c-common.svg-icon icon_name="seax" />'. Compiled by hand because
    "from_string" does not go through the loaders, and the cotton loader is what turns the tag into
    something Django can render.
    """
    return engines["django"].from_string(CottonCompiler().process(tag)).render(context)


def parse(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")
