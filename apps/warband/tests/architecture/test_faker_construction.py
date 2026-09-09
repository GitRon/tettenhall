"""
Architectural test for where a ``Faker`` may be built.

The Saxon culture's locale is ``ang``, which is the ISO 639-3 code for Old English and not a Faker
locale - Faker accepts the locales it ships provider data for and refuses the rest before it imports a
single provider. The Old English name stock therefore arrives through ``Faker.add_provider()``, and the
factory in the faction topic is what knows to do that.

So ``Faker([culture.locale])`` written anywhere else raises ``AttributeError`` - but only for the one
culture out of five whose locale Faker has never heard of. Every test that reaches for a culture by
``Culture.objects.first()`` or by a factory gets Norse or ``en_GB`` and stays green, and the crash waits
in the savegame of whoever picks Saxon. That is why this is checked over the sources, once, for every
construction site at all.
"""

import ast
from pathlib import Path

from apps.warband.tests.architecture.discovery import module_path_for, production_module_files

# The one module allowed to build a faker, because it is the one that knows which locales are ours
FAKER_FACTORY_MODULE = "apps.warband.faction.services.faker"

FAKER_CLASS_NAME = "Faker"


def _callee_name(*, callee: ast.expr) -> str | None:
    """
    The name a call is written against, for a plain name and for a dotted one alike.
    """
    if isinstance(callee, ast.Name):
        return callee.id

    if isinstance(callee, ast.Attribute):
        return callee.attr

    return None


def _faker_constructions(*, file: Path) -> list[str]:
    """
    Every place this module calls "Faker", as importable locations.

    Read as syntax rather than as text, so the docstrings explaining why "Faker(["ang"])" raises do not
    count as calls to it.
    """
    tree = ast.parse(file.read_text(encoding="utf-8"))

    return [
        f"{module_path_for(file=file)}:{node.lineno}"
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and _callee_name(callee=node.func) == FAKER_CLASS_NAME
    ]


def test_only_the_factory_builds_a_faker():
    """
    Anything needing a faker asks the factory for one, so the Old English provider is reachable from
    every call site rather than from the one that remembered it.
    """
    violations = [
        location
        for file in production_module_files()
        if module_path_for(file=file) != FAKER_FACTORY_MODULE
        for location in _faker_constructions(file=file)
    ]

    assert violations == []
