"""
Architectural test for savegame scoping in the view layer.

A model-backed view whose queryset is not restricted to the current savegame exposes other
players' data - and on a POST view, lets one player change it. Nothing in Django enforces that,
and the id comes straight from the URL, so this is checked here for every view at once.
"""

import ast
import importlib
import inspect

from django.db.models import Model
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.list import MultipleObjectMixin

from apps.warband.savegame.mixins import PlayerFactionScopedQuerysetMixin, SavegameScopedQuerysetMixin
from apps.warband.savegame.models.savegame import Savegame
from apps.warband.tests.architecture.discovery import module_path_for, view_module_files

# Reaching for a manager directly is fine when the statement narrows the result itself: through one
# of the scoping queryset methods, by passing the current savegame, or by constraining it to
# "self.object", which came from the scoped queryset. Substring matching keeps this readable at the
# price of some slack - a statement merely mentioning one of these passes.
SCOPING_EXPRESSIONS = ("for_savegame", "for_player_faction", "for_user", "current_savegame", "self.object")

# Views which deliberately don't scope by savegame. Every entry needs a reason.
UNSCOPED_VIEWS: frozenset[str] = frozenset(
    {
        # Scope by user instead - these are the views for picking a savegame in the first place
        "SavegameListView",
        "SavegameLoadView",
    }
)

# Views this check cannot see at all. The collection below takes "SingleObjectMixin" and
# "MultipleObjectMixin", because those are what resolve an object from the URL - so a plain
# "TemplateView" that queries a scoped manager itself is outside it, however much scoping it does.
#
# Listed rather than left silent: "UNSCOPED_VIEWS" above states its exceptions and this blind spot
# stated nothing, which is the difference worth closing. Each entry names the test that does cover
# it, and the test below keeps the list from outliving the shape that put a view on it.
UNCOLLECTED_SCOPED_VIEWS: frozenset[str] = frozenset(
    {
        # A "TemplateView" rendering the player faction's month log through "for_player_faction".
        # The id it scopes by comes off the session's current savegame rather than the URL, which is
        # the risk this module exists to catch, and
        # "account/tests/test_views.py::test_dashboard_view_lists_the_month_logs_of_the_player_faction"
        # plants a rival's row in the same savegame and asserts it is excluded.
        "DashboardView",
    }
)


def _project_view_classes() -> list[type]:
    """
    Every view class defined by the project itself.

    Goes through the same file list as the checks below, so an app keeping its views in a package
    rather than a single "views.py" is covered here too instead of being skipped silently.
    """
    view_classes = []

    for file in view_module_files():
        module = importlib.import_module(module_path_for(file=file))

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


def test_views_the_check_cannot_see_are_still_out_of_its_reach():
    """
    Keeps "UNCOLLECTED_SCOPED_VIEWS" honest.

    A view named there is claiming to be outside the collection above, so its scoping is vouched for
    by a test of its own instead. The moment one grows a "SingleObjectMixin" or a
    "MultipleObjectMixin" the claim stops being true, the real check starts covering it, and the
    entry has to come off the list rather than sit there excusing a view nobody excluded.
    """
    collected = {
        view_class.__name__
        for view_class in _project_view_classes()
        if issubclass(view_class, SingleObjectMixin | MultipleObjectMixin)
    }

    assert UNCOLLECTED_SCOPED_VIEWS & collected == set()


def _resolve(*, node: ast.expr, module) -> object | None:
    """
    Resolves a (possibly dotted) name against the namespace of the module it was found in.
    """
    if isinstance(node, ast.Name):
        return getattr(module, node.id, None)

    if isinstance(node, ast.Attribute):
        parent = _resolve(node=node.value, module=module)

        return getattr(parent, node.attr, None) if parent is not None else None

    return None


def _is_model(obj: object) -> bool:
    return isinstance(obj, type) and issubclass(obj, Model)


def _enclosing_statement(*, node: ast.AST, parents: dict) -> ast.AST:
    while node in parents and not isinstance(node, ast.stmt):
        node = parents[node]

    # Only the value side counts: "self.object = Warrior.objects..." would otherwise allow itself,
    # since its assignment target already mentions "self.object"
    if isinstance(node, ast.Assign | ast.AnnAssign) and node.value is not None:
        return node.value

    return node


def _parent_map(*, tree: ast.AST) -> dict:
    return {child: parent for parent in ast.walk(tree) for child in ast.iter_child_nodes(parent)}


def test_shortcut_lookups_in_views_receive_a_queryset():
    """
    get_object_or_404() with a bare model class is unscoped by construction: the id comes from the
    URL, so it reaches every player's objects. Handing it a queryset is what makes it safe.
    """
    violations = []
    for file in view_module_files():
        module = importlib.import_module(module_path_for(file=file))
        tree = ast.parse(file.read_text(encoding="utf-8"))

        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name) or not node.args:
                continue
            if node.func.id not in ("get_object_or_404", "get_list_or_404"):
                continue

            looked_up = _resolve(node=node.args[0], module=module)
            if _is_model(looked_up):
                violations.append(f"{file.name}:{node.lineno} {node.func.id}({looked_up.__name__}, ...)")

    assert violations == []


def test_scoped_views_do_not_bypass_their_own_queryset():
    """
    A view carrying the scoping mixin and then querying a manager directly has scoped nothing - the
    mixin becomes dead code. Reaching for the manager is only fine when the statement narrows the
    queryset itself.
    """
    scoped_view_names = {
        view_class.__name__
        for view_class in _project_view_classes()
        if issubclass(view_class, SavegameScopedQuerysetMixin | PlayerFactionScopedQuerysetMixin)
    }
    violations = []

    for file in view_module_files():
        module = importlib.import_module(module_path_for(file=file))
        tree = ast.parse(file.read_text(encoding="utf-8"))
        parents = _parent_map(tree=tree)

        for class_node in tree.body:
            if not isinstance(class_node, ast.ClassDef) or class_node.name not in scoped_view_names:
                continue

            for node in ast.walk(class_node):
                if not isinstance(node, ast.Attribute) or node.attr != "objects":
                    continue

                owner = _resolve(node=node.value, module=module)
                is_own_model = ast.unparse(node.value) == "self.model"
                if not is_own_model and not (_is_model(owner) and owner is not Savegame):
                    continue

                statement = ast.unparse(_enclosing_statement(node=node, parents=parents))
                if any(expression in statement for expression in SCOPING_EXPRESSIONS):
                    continue

                violations.append(f"{file.name}:{node.lineno} {class_node.name} queries {ast.unparse(node)}")

    assert violations == []
