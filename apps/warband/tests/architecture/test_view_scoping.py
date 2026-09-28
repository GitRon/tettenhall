"""
Architectural test for savegame scoping in the view layer.

A model-backed view whose queryset is not restricted to the current savegame exposes other
players' data - and on a POST view, lets one player change it. Nothing in Django enforces that,
and the id comes straight from the URL, so this is checked here for every view at once.
"""

import ast
import importlib
import inspect
import textwrap

from django.db.models import Model, QuerySet
from django.views import View
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

# Queryset methods which narrow to what the current player may reach: his savegame, his faction, or - for
# the views picking a savegame - his user. A "get_queryset" override has scoped its queryset when every
# one of its returns goes through one of these, ends in ".none()", or builds on a "super().get_queryset()"
# that is scoped itself. Each of them takes the savegame, the faction or the user as an argument, so the
# caller is the one naming whose objects are meant.
SCOPING_QUERYSET_METHODS: frozenset[str] = frozenset(
    {
        "for_savegame",
        "for_player_faction",
        "for_user",
        # The mercenaries in one faction's pub, and the items on one faction's shop shelf
        "in_pub_of",
        "on_sale_at",
        # The rivals of the player of a savegame, narrowed by who can be fought or ridden into
        "rivals_in_play",
        "attackable_by",
        "occupiable_by",
    }
)

# Views which deliberately don't scope by savegame. Every entry needs a reason.
UNSCOPED_VIEWS: frozenset[str] = frozenset(
    {
        # Scope by user instead - these are the views for picking a savegame in the first place
        "SavegameListView",
        "SavegameLoadView",
        # Before and after there is a player at all
        "LoginView",
        "LogoutView",
        # Makes a savegame rather than reading one, so there is none yet to scope by
        "SavegameCreateView",
        # Resolves nothing: the navbar's counters come from the context processors every authenticated
        # page runs, and those read the session's current savegame, never an id from the URL
        "ResourceBarHtmxView",
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
        # A "TemplateView" resolving a skirmish and one of its two sides from the URL, the skirmish through
        # "for_savegame". "skirmish/tests/test_views.py::
        # test_faction_warrior_list_update_htmx_view_cannot_list_warriors_of_another_savegame" asks for a
        # skirmish of another savegame and asserts the 404.
        "FactionWarriorListUpdateHtmxView",
        # A plain "View" turning the session's current savegame to its next month. The one query it runs
        # itself, for open skirmishes, goes through "for_savegame", and
        # "month/tests/test_views.py::test_finish_month_view_ignores_an_open_skirmish_of_another_savegame"
        # leaves another savegame's fight open and asserts the month still turns.
        "FinishMonthView",
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


def _is_super_get_queryset(*, node: ast.AST) -> bool:
    """
    Whether the node is the call "super().get_queryset()".
    """
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "get_queryset"
        and isinstance(node.func.value, ast.Call)
        and isinstance(node.func.value.func, ast.Name)
        and node.func.value.func.id == "super"
    )


def _chained_calls(*, expression: ast.expr) -> list[ast.Call]:
    """
    Every call of a method chain, outermost first: "a.b().c()" gives "c()" and then "b()".
    """
    calls = []
    while isinstance(expression, ast.Call) and isinstance(expression.func, ast.Attribute):
        calls.append(expression)
        expression = expression.func.value

    return calls


def _return_scopes(*, expression: ast.expr, super_scopes: bool) -> bool:
    calls = _chained_calls(expression=expression)
    method_names = {call.func.attr for call in calls}

    if "none" in method_names or method_names & SCOPING_QUERYSET_METHODS:
        return True

    return super_scopes and any(_is_super_get_queryset(node=call) for call in calls)


def _scopes_its_queryset(view_class: type, *, start: int = 0) -> bool:
    """
    Whether the queryset the view resolves its objects from is narrowed to the current player.

    Reads what the effective "get_queryset" override returns rather than whether there is one: an
    override returning "Model.objects.all()" is an override all the same. A return building on
    "super().get_queryset()" is only as scoped as the rest of the MRO, so that is asked next - which is
    how a view ordering the queryset of a scoping mixin passes, and one ordering Django's own does not.
    """
    mro = view_class.__mro__

    for index in range(start, len(mro)):
        function = mro[index].__dict__.get("get_queryset")
        if function is None:
            continue
        if not mro[index].__module__.startswith("apps."):
            return False

        tree = ast.parse(textwrap.dedent(inspect.getsource(function)))
        returned = [node.value for node in ast.walk(tree) if isinstance(node, ast.Return) and node.value is not None]
        super_scopes = _scopes_its_queryset(view_class, start=index + 1)

        return bool(returned) and all(
            _return_scopes(expression=expression, super_scopes=super_scopes) for expression in returned
        )

    return False


def test_model_backed_views_scope_their_queryset():
    unscoped = [
        view_class.__name__
        for view_class in _project_view_classes()
        if issubclass(view_class, SingleObjectMixin | MultipleObjectMixin)
        and view_class.__name__ not in UNSCOPED_VIEWS
        and not _scopes_its_queryset(view_class)
    ]

    assert unscoped == []


def test_scopes_its_queryset_refuses_an_override_returning_every_object():
    class Leaky(SingleObjectMixin):
        def get_queryset(self) -> QuerySet:
            return Savegame.objects.all()

    assert _scopes_its_queryset(Leaky) is False


def test_scopes_its_queryset_accepts_a_scoping_queryset_method():
    class Narrowed(SingleObjectMixin):
        def get_queryset(self) -> QuerySet:
            return Savegame.objects.for_user(user_id=self.request.user.id)

    assert _scopes_its_queryset(Narrowed) is True


def test_scopes_its_queryset_accepts_building_on_a_scoping_mixin():
    class Ordered(SavegameScopedQuerysetMixin, SingleObjectMixin):
        def get_queryset(self) -> QuerySet:
            return super().get_queryset().order_by("id")

    assert _scopes_its_queryset(Ordered) is True


def test_scopes_its_queryset_refuses_building_on_djangos_own_queryset():
    class Ordered(SingleObjectMixin):
        def get_queryset(self) -> QuerySet:
            return super().get_queryset().order_by("id")

    assert _scopes_its_queryset(Ordered) is False


def test_scopes_its_queryset_refuses_an_override_with_one_unscoped_return():
    class HalfScoped(SingleObjectMixin):
        def get_queryset(self) -> QuerySet:
            if self.request is None:
                return Savegame.objects.none()
            return Savegame.objects.all()

    assert _scopes_its_queryset(HalfScoped) is False


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


def test_every_view_the_check_cannot_see_is_listed():
    """
    Keeps the two lists above complete. A view outside the collection is checked by nothing here, so it
    has to say why: "UNCOLLECTED_SCOPED_VIEWS" names the test vouching for its scoping, "UNSCOPED_VIEWS"
    the reason it has none to do.
    """
    unlisted = sorted(
        view_class.__name__
        for view_class in _project_view_classes()
        if issubclass(view_class, View)
        and not issubclass(view_class, SingleObjectMixin | MultipleObjectMixin)
        and view_class.__name__ not in UNCOLLECTED_SCOPED_VIEWS | UNSCOPED_VIEWS
    )

    assert unlisted == []


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


def _get_object_bypasses(*, tree: ast.AST) -> list[str]:
    """
    Every "get_object()" defined on a class that calls "super().get_queryset()".
    """
    violations = []

    for class_node in ast.walk(tree):
        if not isinstance(class_node, ast.ClassDef):
            continue

        for method in class_node.body:
            if not isinstance(method, ast.FunctionDef) or method.name != "get_object":
                continue

            violations.extend(
                f"{class_node.name}:{node.lineno}" for node in ast.walk(method) if _is_super_get_queryset(node=node)
            )

    return violations


def test_get_object_bypasses_names_a_get_object_calling_super_get_queryset():
    source = (
        "class Leaky:\n"
        "    def get_object(self, queryset=None):\n"
        "        return super().get_queryset().first()\n"
        "\n"
        "class Safe:\n"
        "    def get_object(self, queryset=None):\n"
        "        return self.get_queryset().first()\n"
    )

    result = _get_object_bypasses(tree=ast.parse(source))

    assert result == ["Leaky:3"]


def test_get_object_does_not_skip_the_scoped_queryset():
    """
    The first trap of "docs/patterns/savegame-scoping.md". When the scoping lives on the view class
    itself, "super().get_queryset()" inside "get_object()" steps past it and resolves the id from the URL
    against every player's objects - while the scoping override sits right there, looking applied.
    """
    violations = [
        f"{file.name} {violation}"
        for file in view_module_files()
        for violation in _get_object_bypasses(tree=ast.parse(file.read_text(encoding="utf-8")))
    ]

    assert violations == []
