"""
Architectural test for the admin registrations of the topic packages.

Django's admin autodiscovery imports "<app>/admin.py" and nothing below it, so a topic's "admin.py"
reaches the admin site only through an import in the app root's. One left out loses its pages with no
error anywhere - see "docs/patterns/app-layout.md" - so every one of them is checked here at once.
"""

import ast
from pathlib import Path

from apps.warband.tests.architecture.discovery import module_path_for, project_app_configs

ADMIN_MODULE_FILE_NAME = "admin.py"


def _imported_modules(*, tree: ast.AST) -> set[str]:
    imported = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported.add(node.module)
            imported.update(f"{node.module}.{alias.name}" for alias in node.names)

    return imported


def _unimported_topic_admins(*, app_path: Path) -> list[str]:
    root_admin = app_path / ADMIN_MODULE_FILE_NAME
    imported = (
        _imported_modules(tree=ast.parse(root_admin.read_text(encoding="utf-8"))) if root_admin.exists() else set()
    )

    return sorted(
        module_path
        for file in app_path.rglob(ADMIN_MODULE_FILE_NAME)
        if file != root_admin and "tests" not in file.relative_to(app_path).parts
        for module_path in (module_path_for(file=file),)
        if module_path not in imported
    )


def test_imported_modules_reads_both_import_spellings():
    source = "import apps.warband.faction.admin\nfrom apps.warband.item import admin\n"

    result = _imported_modules(tree=ast.parse(source))

    assert result == {"apps.warband.faction.admin", "apps.warband.item", "apps.warband.item.admin"}


def test_every_topic_admin_is_imported_by_the_app_root():
    unimported = [
        module_path
        for app_config in project_app_configs()
        for module_path in _unimported_topic_admins(app_path=Path(app_config.path))
    ]

    assert unimported == []
