"""
Where the component tests find components, what each declares, and where each is called.

Everything is read with cotton's own compiler and tag parser rather than a regex of our own, so a call
site the library would render is a call site these tests see, and the other way round.

See docs/patterns/components.md.
"""

import re
from dataclasses import dataclass
from pathlib import Path

from django.conf import settings
from django_cotton.compiler_regex import CottonCompiler
from django_cotton.tag_parser import parse_component_tag, parse_vars_tag

from apps.warband.tests.architecture.discovery import project_app_configs

COMPONENT_DIRECTORY_NAME = "cotton"

# The compiled form of "<c-vars ...>" and of a "<c-name ...>" opening tag. The closing "{% endcotton %}"
# carries nothing, and "{% cotton:slot %}" is a slot rather than a call.
COMPILED_VARS_PATTERN = re.compile(r"{% (cotton:vars\b.*?) %}", re.DOTALL)
COMPILED_CALL_PATTERN = re.compile(r"{% (cotton [^:].*?) %}", re.DOTALL)


@dataclass(frozen=True, kw_only=True)
class Component:
    name: str
    file: Path
    required: frozenset[str]
    defaulted: frozenset[str]

    @property
    def declared(self) -> frozenset[str]:
        return self.required | self.defaulted


@dataclass(frozen=True, kw_only=True)
class CallSite:
    location: str
    name: str
    attributes: frozenset[str]


def component_name_for(*, file: Path, cotton_directory: Path) -> str:
    """
    The tag a component is called by: folders become dots and underscores hyphens, the way cotton
    resolves "<c-common.svg-icon>" to "cotton/common/svg_icon.html".
    """
    parts = file.relative_to(cotton_directory).with_suffix("").parts

    return ".".join(parts).replace("_", "-")


def declared_vars(*, content: str) -> tuple[frozenset[str], frozenset[str]]:
    """
    A component's parameters as (required, defaulted). A name in "<c-vars>" without a value has no
    default, so every call site has to pass it.
    """
    match = COMPILED_VARS_PATTERN.search(CottonCompiler().process(content))
    if match is None:
        return frozenset(), frozenset()

    result = parse_vars_tag(match.group(1))

    return frozenset(result.empty_attrs), frozenset(result.attrs)


def call_sites_in(*, content: str, file_name: str) -> list[CallSite]:
    """
    Every component call in one template. A ":" in front of an attribute only says how its value is
    read, so it is not part of the parameter's name.
    """
    compiled = CottonCompiler().process(content)
    call_sites = []

    for match in COMPILED_CALL_PATTERN.finditer(compiled):
        result = parse_component_tag(match.group(1))
        call_sites.append(
            CallSite(
                location=f"{file_name}:{compiled.count('\n', 0, match.start()) + 1}",
                name=result.name,
                attributes=frozenset(attribute.lstrip(":") for attribute in result.attrs),
            )
        )

    return call_sites


def component_files() -> list[tuple[str, Path]]:
    """
    Every component in every local app, as (name, file). A list rather than a mapping, because the same
    name in two apps is exactly what a test has to be able to see.
    """
    components = []

    for app_config in project_app_configs():
        cotton_directory = Path(app_config.path) / "templates" / COMPONENT_DIRECTORY_NAME
        components.extend(
            (component_name_for(file=file, cotton_directory=cotton_directory), file)
            for file in sorted(cotton_directory.glob("**/*.html"))
        )

    return components


def components() -> dict[str, Component]:
    result = {}

    for name, file in component_files():
        required, defaulted = declared_vars(content=file.read_text(encoding="utf-8"))
        result[name] = Component(name=name, file=file, required=required, defaulted=defaulted)

    return result


def call_sites() -> list[CallSite]:
    # Every app ships its templates under its own "templates/" directory - "DIRS" is empty - so there is
    # no second place for a call site to hide
    files = sorted((Path(settings.BASE_DIR) / "apps").glob("**/templates/**/*.html"))

    return [
        call_site
        for file in files
        for call_site in call_sites_in(content=file.read_text(encoding="utf-8"), file_name=file.name)
    ]


def unknown_components(*, call_sites: list[CallSite], components: dict[str, Component]) -> list[str]:
    return [
        f"{call_site.location}: <c-{call_site.name}>" for call_site in call_sites if call_site.name not in components
    ]


def undeclared_attributes(*, call_sites: list[CallSite], components: dict[str, Component]) -> list[str]:
    """
    An attribute the component does not declare is no error to cotton: it lands in "attrs" and is
    dropped, so a misspelt parameter renders as the default and fails nowhere.
    """
    violations = []

    for call_site in call_sites:
        component = components.get(call_site.name)
        if component is None:
            continue
        violations.extend(
            f"{call_site.location}: <c-{call_site.name}> passes {attribute!r}"
            for attribute in sorted(call_site.attributes - component.declared)
        )

    return violations


def missing_required_attributes(*, call_sites: list[CallSite], components: dict[str, Component]) -> list[str]:
    """
    A required parameter that is not passed is no error either: components see the caller's context,
    so the parameter quietly takes whatever the caller happens to have under that name.
    """
    violations = []

    for call_site in call_sites:
        component = components.get(call_site.name)
        if component is None:
            continue
        violations.extend(
            f"{call_site.location}: <c-{call_site.name}> leaves out {attribute!r}"
            for attribute in sorted(component.required - call_site.attributes)
        )

    return violations


def duplicate_component_names(*, component_files: list[tuple[str, Path]]) -> list[str]:
    """
    Both apps share the one "cotton/" namespace, and the template loader takes the first app that has
    the file, so the second one is shadowed without a word.
    """
    seen: dict[str, Path] = {}
    duplicates = []

    for name, file in component_files:
        if name in seen:
            duplicates.append(f"<c-{name}>: {seen[name]} and {file}")
        else:
            seen[name] = file

    return duplicates
