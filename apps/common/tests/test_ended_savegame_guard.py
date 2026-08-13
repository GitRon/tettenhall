"""
Architectural test for the guard that closes a finished savegame.

A view that dispatches a command changes the world, and a savegame that has been won or lost must not
change any more. One unit test on the mixin proves it refuses; it cannot prove that all seven views
actually carry it, and forgetting one is silent - the view keeps working, just in a game that is over.
"""

import ast
import importlib
from pathlib import Path

from django.apps import apps
from django.conf import settings

from apps.savegame.mixins import RunningSavegameRequiredMixin

# Views which dispatch a command and still have to work once the game is decided. Both are how a
# player leaves a finished savegame behind, so guarding them would trap him in it.
UNGUARDED_VIEWS: frozenset[str] = frozenset(
    {
        "SavegameCreateView",
        "SavegameLoadView",
    }
)


def _view_module_files() -> list[Path]:
    base_path = (Path(settings.BASE_DIR) / "apps").resolve()
    files = []

    for app_config in apps.get_app_configs():
        app_path = Path(app_config.path).resolve()
        if base_path not in app_path.parents:
            continue
        files.extend(sorted(app_path.glob("views.py")))
        files.extend(sorted(app_path.glob("views/**/*.py")))

    return [file for file in files if file.stem != "__init__"]


def _module_path_for(*, file: Path) -> str:
    parts = file.resolve().relative_to(Path(settings.BASE_DIR).resolve()).with_suffix("").parts
    if parts[-1] == "__init__":
        parts = parts[:-1]

    return ".".join(parts)


def _dispatching_view_classes() -> list[type]:
    """
    Every view class whose body calls handle_message().
    """
    view_classes = []

    for file in _view_module_files():
        module = importlib.import_module(_module_path_for(file=file))
        tree = ast.parse(file.read_text(encoding="utf-8"))

        for class_node in tree.body:
            if not isinstance(class_node, ast.ClassDef):
                continue

            dispatches = any(
                isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "handle_message"
                for node in ast.walk(class_node)
            )
            if dispatches:
                view_classes.append(getattr(module, class_node.name))

    return view_classes


def test_every_view_dispatching_a_command_refuses_a_finished_savegame():
    unguarded = [
        view_class.__name__
        for view_class in _dispatching_view_classes()
        if view_class.__name__ not in UNGUARDED_VIEWS and RunningSavegameRequiredMixin not in view_class.__mro__
    ]

    assert unguarded == []


def test_the_guard_covers_every_view_that_dispatches_a_command():
    """
    Guards the test above against quietly measuring nothing: an import mistake or a renamed helper
    would leave the list empty and the assertion green.
    """
    assert len(_dispatching_view_classes()) >= len(UNGUARDED_VIEWS) + 7
