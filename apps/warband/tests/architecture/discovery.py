"""
Where the architecture tests look for code.

One helper rather than a copy per test module. The three that used to carry their own version
disagreed on two things - glob depth, and whether ``__init__.py`` counts - which is how a view
defined in a ``views/`` package came to be checked for savegame scoping and skipped by the
finished-savegame guard. Both questions are settled here, once: the walk is recursive, and
``__init__.py`` is always included, because a view nobody collects is a view nobody checks.

Handler discovery deliberately mirrors queuebie's own and reads the library's exclusion setting
rather than restating it, so a test cannot drift from what the bus actually imports.
"""

from pathlib import Path

from django.apps import apps
from django.conf import settings
from queuebie.settings import get_queuebie_excluded_directories
from queuebie.utils import HANDLERS_DIRECTORY_NAME

MESSAGE_TYPE_DIRECTORY_NAMES = ("commands", "events")


def project_app_configs() -> list:
    """
    App configs of the local apps, ignoring everything installed as a dependency.

    Matched against "apps/" rather than BASE_DIR: uv puts the virtualenv in ".venv/" inside the
    project, so BASE_DIR is also a parent of every installed package - django.contrib.admin
    included, which then gets collected as one of ours.
    """
    apps_path = (Path(settings.BASE_DIR) / "apps").resolve()

    return [app_config for app_config in apps.get_app_configs() if apps_path in Path(app_config.path).resolve().parents]


def module_path_for(*, file: Path) -> str:
    """
    Turns an absolute file path into its importable dotted module path.
    """
    relative_path = file.resolve().relative_to(Path(settings.BASE_DIR).resolve())
    parts = relative_path.with_suffix("").parts

    # A package is imported by its own name, so the trailing "__init__" has to come off or identity
    # checks against a class's "__module__" never match.
    if parts[-1] == "__init__":
        parts = parts[:-1]

    return ".".join(parts)


def _is_excluded(*, path: Path, app_path: Path, excluded: set[str]) -> bool:
    return bool(excluded & set(path.relative_to(app_path).parts))


def handler_files() -> list[Path]:
    """
    All modules queuebie collects its handlers from.

    The domain app keeps its handlers in topic packages below the app root, so this walks the whole
    subtree the way autodiscovery does instead of looking only at "<app>/handlers/".
    """
    excluded = get_queuebie_excluded_directories()
    files: list[Path] = []

    for app_config in project_app_configs():
        app_path = Path(app_config.path).resolve()
        for handlers_path in sorted(app_path.rglob(HANDLERS_DIRECTORY_NAME)):
            if not handlers_path.is_dir() or _is_excluded(path=handlers_path, app_path=app_path, excluded=excluded):
                continue
            for message_type in MESSAGE_TYPE_DIRECTORY_NAMES:
                files.extend(sorted((handlers_path / message_type).glob("*.py")))

    return [file for file in files if file.stem != "__init__"]


def production_module_files() -> list[Path]:
    """
    Every module under "apps/" that ships, tests and migrations excluded.

    Walked from the directory rather than from the app configs, because not everything under "apps/"
    is an app: a satellite that registers with something other than Django owns no app config and
    would be missed by a walk that starts from one.
    """
    excluded = get_queuebie_excluded_directories()
    apps_path = (Path(settings.BASE_DIR) / "apps").resolve()

    return sorted(
        path for path in apps_path.rglob("*.py") if not _is_excluded(path=path, app_path=apps_path, excluded=excluded)
    )


def view_module_files() -> list[Path]:
    """
    Every module a view class can be defined in, at any depth below an app root.

    ``__init__.py`` is kept rather than filtered: a view put straight into ``views/__init__.py`` or
    into a nested subpackage would otherwise be collected by nothing and escape every check.
    """
    excluded = get_queuebie_excluded_directories()
    files: list[Path] = []

    for app_config in project_app_configs():
        app_path = Path(app_config.path).resolve()
        candidates = sorted(app_path.rglob("views.py")) + sorted(app_path.rglob("views/**/*.py"))
        files.extend(path for path in candidates if not _is_excluded(path=path, app_path=app_path, excluded=excluded))

    return sorted(set(files))
