"""
Architectural test for savegame scoping in the view layer.

A model-backed view whose queryset is not restricted to the current savegame exposes other
players' data - and on a POST view, lets one player change it. Nothing in Django enforces that,
and the id comes straight from the URL, so this is checked here for every view at once.
"""

import importlib
import inspect
from pathlib import Path

from django.apps import apps
from django.conf import settings
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.list import MultipleObjectMixin

# Views which deliberately don't scope by savegame. Every entry needs a reason.
UNSCOPED_VIEWS: frozenset[str] = frozenset(
    {
        # Scope by user instead - these are the views for picking a savegame in the first place
        "SavegameListView",
        "SavegameLoadView",
    }
)


def _project_view_classes() -> list[type]:
    """
    Every view class defined by the project itself.
    """
    base_path = Path(settings.BASE_DIR).resolve()
    view_classes = []

    for app_config in apps.get_app_configs():
        if base_path not in Path(app_config.path).resolve().parents:
            continue

        try:
            module = importlib.import_module(f"{app_config.name}.views")
        except ModuleNotFoundError:
            continue

        for attribute in vars(module).values():
            if inspect.isclass(attribute) and attribute.__module__ == module.__name__:
                view_classes.append(attribute)

    return view_classes


def _scopes_its_queryset(view_class: type) -> bool:
    """
    Whether the view narrows its queryset itself, either directly or through one of our mixins.
    """
    return any(
        "get_queryset" in klass.__dict__ and klass.__module__.startswith("apps.") for klass in view_class.__mro__
    )


def test_model_backed_views_scope_their_queryset():
    unscoped = [
        view_class.__name__
        for view_class in _project_view_classes()
        if issubclass(view_class, SingleObjectMixin | MultipleObjectMixin)
        and view_class.__name__ not in UNSCOPED_VIEWS
        and not _scopes_its_queryset(view_class)
    ]

    assert unscoped == []
