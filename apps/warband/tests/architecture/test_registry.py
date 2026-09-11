"""
Wiring tests for the queuebie message registry.

Unit tests can only ever verify a single handler. Whether the handlers actually form a chain is
decided at runtime by the registry, so neither the IDE nor a type checker will notice when a
message is emitted that nobody consumes. These five tests cover all of those edges at once.
"""

import ast
import dataclasses
import importlib
from pathlib import Path

from queuebie.messages import Command, Event

from apps.warband.tests.architecture.discovery import handler_files, module_path_for, view_module_files

# Events which are deliberately emitted without a consumer. All of them announce a state change
# their emitting command handler has already carried out, so nobody has to react - they exist so
# something can subscribe later. Commands are never allowlisted, see the tests at the bottom.
TERMINAL_MESSAGES: frozenset[str] = frozenset(
    {
        "apps.warband.faction.messages.events.faction.NewLeaderWarriorSet",
        "apps.warband.faction.messages.events.warrior.WarriorWasAddedToPub",
        "apps.warband.faction.messages.events.item.ItemWasAddedToShop",
        "apps.warband.faction.messages.events.item.ItemWasRemovedFromShop",
        # The three levers an incident pulls in somebody else's app. Each announces a change its own
        # command handler has already made, and the incident wrote the player's line about it before
        # any of them ran - a consumer here would be a second line for one event
        "apps.warband.faction.messages.events.faction.FyrdReserveChanged",
        "apps.warband.item.messages.events.item.ItemWasLost",
        "apps.warband.warrior.messages.events.warrior.WarriorMaxMoraleChanged",
        "apps.warband.finance.messages.events.transaction.TransactionCreated",
        "apps.warband.item.messages.events.item.OwnershipChanged",
        "apps.warband.month.messages.events.month.PlayerMonthLogCleared",
        "apps.warband.month.messages.events.month.PlayerMonthLogCreated",
        "apps.warband.quest.messages.events.quest.NewQuestCreated",
        "apps.warband.quest.messages.events.quest_contract.QuestContractAsActiveQuestRemoved",
        "apps.warband.quest.messages.events.quest_contract.SkirmishToQuestContractAssigned",
        "apps.warband.skirmish.messages.events.battle_history.BattleHistoryCreated",
        "apps.warband.skirmish.messages.events.skirmish_report.SkirmishBlowRecorded",
        "apps.warband.skirmish.messages.events.skirmish_report.SkirmishCasualtyRecorded",
        "apps.warband.skirmish.messages.events.skirmish_report.SkirmishSpoilRecorded",
        "apps.warband.skirmish.messages.events.skirmish_report.WarriorGrowthRecorded",
        "apps.warband.skirmish.messages.events.warrior.LastUsedSkirmishActionStored",
        "apps.warband.training.messages.events.training.NewTrainingCreated",
    }
)


def _emitting_files() -> list[Path]:
    """
    All modules which can put a message into the queue: the handlers plus the views kicking a
    queue run off in the first place.
    """
    files = handler_files() + view_module_files()

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
        module = importlib.import_module(module_path_for(file=file))
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
    for file in handler_files():
        module_path = module_path_for(file=file)
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
    for file in handler_files():
        module_path = module_path_for(file=file)
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


def test_every_command_has_exactly_one_handler(queuebie_registry):
    """
    A command names the one piece of work it wants done, so a second handler on it is a second
    answer to a question that has one. Events are the message type that fans out - see the handler
    docs - and nothing but this notices when a command starts behaving like one.
    """
    commands_with_several_handlers = {
        message_path: sorted(f"{definition['module']}.{definition['name']}" for definition in handler_list)
        for message_path, handler_list in queuebie_registry.command_dict.items()
        if len(handler_list) > 1
    }

    assert commands_with_several_handlers == {}


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


def _command_module_mismatches(*, registry) -> list[str]:
    """
    Every command whose handler sits in a module named differently from the command's own.
    """
    mismatches = []

    for command_path, handler_list in registry.command_dict.items():
        command_module, class_name = command_path.rsplit(".", 1)
        domain = command_module.rsplit(".", 1)[-1]

        for definition in handler_list:
            if definition["module"].rsplit(".", 1)[-1] != domain:
                mismatches.append(f"{class_name} is defined in {command_module} but handled in {definition['module']}")

    return mismatches


def test_a_command_is_handled_in_the_module_named_after_the_one_defining_it(queuebie_registry):
    """
    Which module a message belongs in is a judgement call about its subject, see
    "docs/patterns/app-layout.md". That a command and its handler agree on the answer is not, and
    nothing else notices when they drift: queuebie discovers by directory, so a command handled two
    modules away wires up and runs exactly the same.
    """
    mismatches = _command_module_mismatches(registry=queuebie_registry)

    assert mismatches == []
