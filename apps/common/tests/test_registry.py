"""
Wiring tests for the queuebie message registry.

Unit tests can only ever verify a single handler. Whether the handlers actually form a chain is
decided at runtime by the registry, so neither the IDE nor a type checker will notice when a
message is emitted that nobody consumes. These four tests cover all of those edges at once.
"""

import ast
import dataclasses
import importlib
from pathlib import Path

from django.apps import apps
from django.conf import settings
from queuebie.messages import Command, Event

# Events which are deliberately emitted without a consumer. All of them announce a state change
# their emitting command handler has already carried out, so nobody has to react - they exist so
# something can subscribe later. Commands are never allowlisted, see the tests at the bottom.
TERMINAL_MESSAGES: frozenset[str] = frozenset(
    {
        "apps.faction.messages.events.faction.NewLeaderWarriorSet",
        "apps.faction.messages.events.faction.QuestWasRemovedFromBulletinBoard",
        "apps.faction.messages.events.faction.WarriorWasAddedToPub",
        "apps.faction.messages.events.item.ItemWasAddedToShop",
        "apps.faction.messages.events.item.ItemWasRemovedFromShop",
        "apps.finance.messages.events.transaction.TransactionCreated",
        "apps.item.messages.events.item.OwnershipChanged",
        "apps.month.messages.events.month.PlayerMonthLogCleared",
        "apps.month.messages.events.month.PlayerMonthLogCreated",
        "apps.quest.messages.events.quest.NewQuestCreated",
        "apps.quest.messages.events.quest_contract.QuestContractAsActiveQuestRemoved",
        "apps.quest.messages.events.quest_contract.SkirmishToQuestContractAssigned",
        "apps.skirmish.messages.events.battle_history.BattleHistoryCreated",
        "apps.skirmish.messages.events.warrior.LastUsedSkirmishActionStored",
        "apps.training.messages.events.training.NewTrainingCreated",
    }
)


def _project_app_configs() -> list:
    """
    App configs of the local apps, ignoring everything installed as a dependency.

    Matched against "apps/" rather than BASE_DIR: uv puts the virtualenv in ".venv/" inside the
    project, so BASE_DIR is also a parent of every installed package.
    """
    apps_path = (Path(settings.BASE_DIR) / "apps").resolve()

    return [app_config for app_config in apps.get_app_configs() if apps_path in Path(app_config.path).resolve().parents]


def _module_path_for(*, file: Path) -> str:
    """
    Turns an absolute file path into its importable dotted module path.
    """
    relative_path = file.resolve().relative_to(Path(settings.BASE_DIR).resolve())

    return ".".join(relative_path.with_suffix("").parts)


def _handler_files() -> list[Path]:
    """
    All modules queuebie collects its handlers from.
    """
    files = []
    for app_config in _project_app_configs():
        app_path = Path(app_config.path).resolve()
        for message_type in ("commands", "events"):
            files.extend(sorted((app_path / "handlers" / message_type).glob("*.py")))

    return [file for file in files if file.stem != "__init__"]


def _emitting_files() -> list[Path]:
    """
    All modules which can put a message into the queue: the handlers plus the views kicking a
    queue run off in the first place.
    """
    files = list(_handler_files())
    for app_config in _project_app_configs():
        app_path = Path(app_config.path).resolve()
        files.extend(sorted(app_path.glob("views.py")))
        files.extend(sorted(app_path.glob("views/*.py")))

    return [file for file in files if file.stem != "__init__"]


def _resolve(*, node: ast.expr, module) -> object | None:
    """
    Resolves a (possibly dotted) name from the syntax tree against the namespace of the module it
    was found in.

    Going through the imported module instead of comparing names is what makes this reliable: the
    project mixes ``from x import Command`` with ``from x import module`` plus ``module.Command``,
    and a name-based lookup cannot tell those apart.
    """
    if isinstance(node, ast.Name):
        return getattr(module, node.id, None)

    if isinstance(node, ast.Attribute):
        parent = _resolve(node=node.value, module=module)

        return getattr(parent, node.attr, None) if parent is not None else None

    return None


def _emitted_message_paths(*, message_type: type) -> set[str]:
    """
    Collects every message of the given type that gets instantiated - looking at the actual code
    instead of the return annotations, which are declared abstractly (``-> Event``) throughout the
    project.
    """
    emitted = set()
    for file in _emitting_files():
        module = importlib.import_module(_module_path_for(file=file))
        tree = ast.parse(file.read_text(encoding="utf-8"))

        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue

            message_class = _resolve(node=node.func, module=module)
            if isinstance(message_class, type) and issubclass(message_class, message_type):
                emitted.add(message_class.module_path())

    return emitted


def _is_registry_decorator(*, node: ast.expr) -> bool:
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr in ("register_command", "register_event")
    )


def _decorated_handlers() -> set[tuple[str, str]]:
    """
    All handler functions decorated with one of the registration decorators.
    """
    handlers = set()
    for file in _handler_files():
        module_path = _module_path_for(file=file)
        tree = ast.parse(file.read_text(encoding="utf-8"))

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and any(
                _is_registry_decorator(node=decorator) for decorator in node.decorator_list
            ):
                handlers.add((module_path, node.name))

    return handlers


def _message_class_for(*, module_path: str) -> type:
    module_name, class_name = module_path.rsplit(".", 1)

    return getattr(importlib.import_module(module_name), class_name)


def _handler_nodes() -> dict[tuple[str, str], ast.FunctionDef]:
    """
    Syntax tree node of every function in the handler modules, keyed like the registry keys them.
    """
    nodes = {}
    for file in _handler_files():
        module_path = _module_path_for(file=file)
        tree = ast.parse(file.read_text(encoding="utf-8"))

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                nodes[(module_path, node.name)] = node

    return nodes


def _accessed_context_attributes(*, node: ast.FunctionDef) -> set[str]:
    return {
        child.attr
        for child in ast.walk(node)
        if isinstance(child, ast.Attribute) and isinstance(child.value, ast.Name) and child.value.id == "context"
    }


def test_autodiscovery_finds_every_handler(queuebie_registry):
    registered_handlers = {
        (definition["module"], definition["name"])
        for registry in (queuebie_registry.command_dict, queuebie_registry.event_dict)
        for handler_list in registry.values()
        for definition in handler_list
    }

    assert _decorated_handlers() == registered_handlers


def test_every_emitted_command_has_a_handler(queuebie_registry):
    """
    A command is an instruction to do something, so one without a handler is always a bug - which
    is why there is deliberately no allowlist here.
    """
    emitted_commands = _emitted_message_paths(message_type=Command)

    assert emitted_commands - set(queuebie_registry.command_dict) == set()


def test_every_emitted_event_is_either_consumed_or_terminal(queuebie_registry):
    emitted_events = _emitted_message_paths(message_type=Event)

    assert emitted_events - set(queuebie_registry.event_dict) - TERMINAL_MESSAGES == set()


def _context_attribute_violations(*, registry) -> list[str]:
    """
    Every attribute a handler reads off its message which one of the messages it is registered for
    does not carry.
    """
    handler_nodes = _handler_nodes()
    violations = []

    for message_dict in (registry.command_dict, registry.event_dict):
        for message_path, handler_list in message_dict.items():
            message_class = _message_class_for(module_path=message_path)
            if not dataclasses.is_dataclass(message_class):
                continue

            available_attributes = {field.name for field in dataclasses.fields(message_class)} | {"uuid"}

            for definition in handler_list:
                handler_node = handler_nodes[(definition["module"], definition["name"])]
                for attribute in sorted(_accessed_context_attributes(node=handler_node) - available_attributes):
                    violations.append(f"{definition['name']}() reads 'context.{attribute}', absent on {message_path}")

    return violations


def test_handlers_only_read_attributes_all_of_their_messages_carry(queuebie_registry):
    """
    A handler can be registered for more than one message by stacking the decorators. Which
    messages those are only exists in the registry, so nothing points out that a handler reads an
    attribute just one of them carries - it fails at runtime once the other one is dispatched.
    """
    violations = _context_attribute_violations(registry=queuebie_registry)

    assert violations == []
