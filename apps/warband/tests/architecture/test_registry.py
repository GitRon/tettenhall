"""
Wiring tests for the queuebie message registry.

Unit tests can only ever verify a single handler. Whether the handlers actually form a chain is
decided at runtime by the registry, so neither the IDE nor a type checker will notice when a
message is emitted that nobody consumes. These tests cover all of those edges at once.
"""

import ast
import dataclasses
import importlib
import types
import typing
from pathlib import Path
from typing import ForwardRef

from django.db.models import QuerySet
from queuebie.messages import Command, Event

from apps.warband.faction.messages.events.warrior import WarriorMonthPrepared
from apps.warband.skirmish.handlers.commands.skirmish import _withdrawing_and_remaining
from apps.warband.skirmish.messages.commands.warrior import WithdrawFromSkirmish
from apps.warband.skirmish.models.warrior import Warrior
from apps.warband.tests.architecture.discovery import (
    handler_files,
    module_path_for,
    production_module_files,
    view_module_files,
)
from apps.warband.warrior.messages.commands.warrior import HealInjuredWarrior

# Events which are deliberately emitted without a consumer, each with the reason nobody reacts. All of them
# announce a state change their emitting command handler has already carried out - they exist so something
# can subscribe later. Commands are never allowlisted, see the tests at the bottom.
#
# A dict rather than a set with comments beside it, so "every entry carries a reason" is something the
# test below can hold instead of something a reviewer has to count.
_RECORD_WRITTEN = (
    "A record of something that already happened, written to be read back as history. It is the end of "
    "its chain: a reaction to a record being written would be a record about a record."
)
_SHELF_CHANGED = (
    "One row of a pub or shop changing hands. The month log speaks for a restock as a whole "
    "(TownMercenariesRestocked, TownShopRestocked), and the pages read the relation when they render."
)
_CONTRACT_BOOKKEEPING = (
    "Bookkeeping on a quest contract the skirmish drives. The reward and the report both hang off "
    "SkirmishFinished, which carries the contract itself."
)
_INCIDENT_LEVER = (
    "One of the levers an incident pulls in somebody else's topic. It announces a change its own command "
    "handler has already made, and the incident wrote the player's line about it before it ran - a "
    "consumer here would be a second line for one event. The third lever, WarriorMaxMoraleChanged, is "
    "consumed: the relic is the largest gain in nerve the game hands out and can be what first makes a man "
    "worth naming, so the epithet ratchet listens to it - see [handle_raised_ceiling_earns_a_nickname]."
)
TERMINAL_MESSAGES: dict[str, str] = {
    "apps.warband.faction.messages.events.faction.NewLeaderWarriorSet": (
        "Everything that asks who leads a faction reads faction.leader when it needs to, so there is nothing to push."
    ),
    "apps.warband.faction.messages.events.warrior.WarriorWasAddedToPub": _SHELF_CHANGED,
    "apps.warband.faction.messages.events.item.ItemWasAddedToShop": _SHELF_CHANGED,
    "apps.warband.faction.messages.events.item.ItemWasRemovedFromShop": _SHELF_CHANGED,
    "apps.warband.faction.messages.events.faction.FyrdReserveChanged": _INCIDENT_LEVER,
    "apps.warband.item.messages.events.item.ItemWasLost": _INCIDENT_LEVER,
    "apps.warband.incident.messages.events.incident.IncidentAsked": (
        "A question waits on its pending row, and the dashboard reads it from there. What reaches the levers "
        "and the log is the IncidentOccurred its answer raises, not the asking."
    ),
    "apps.warband.item.messages.events.item.ItemEquipped": (
        "The player is looking at the screen that changed, and both entry points already say the part he "
        "cannot see - who the item came off - in a line of their own. A chronicle entry per handout would "
        "bury the month log under the shuffling a single new sword sets off."
    ),
    "apps.warband.finance.messages.events.transaction.TransactionCreated": _RECORD_WRITTEN,
    "apps.warband.item.messages.events.item.OwnershipChanged": (
        "Raised for loot changing hands after a fight, which the spoils of the skirmish report already "
        "record. Who owns an item is read off the item."
    ),
    "apps.warband.month.messages.events.month.PlayerMonthLogCleared": (
        "Housekeeping at the turn of the month: the lines of past months are gone, and nobody had anything "
        "left to do with them."
    ),
    "apps.warband.month.messages.events.month.PlayerMonthLogCreated": _RECORD_WRITTEN,
    "apps.warband.quest.messages.events.quest.NewQuestCreated": (
        "The bulletin board speaks for the batch through BulletinBoardQuestsOffered; one quest being written "
        "adds nothing to that."
    ),
    "apps.warband.quest.messages.events.quest_contract.QuestContractAsActiveQuestRemoved": _CONTRACT_BOOKKEEPING,
    "apps.warband.quest.messages.events.quest_contract.SkirmishToQuestContractAssigned": _CONTRACT_BOOKKEEPING,
    "apps.warband.skirmish.messages.events.battle_history.BattleHistoryCreated": _RECORD_WRITTEN,
    "apps.warband.skirmish.messages.events.skirmish_report.SkirmishBlowRecorded": _RECORD_WRITTEN,
    "apps.warband.skirmish.messages.events.skirmish_report.SkirmishCasualtyRecorded": _RECORD_WRITTEN,
    "apps.warband.skirmish.messages.events.skirmish_report.SkirmishSpoilRecorded": _RECORD_WRITTEN,
    "apps.warband.skirmish.messages.events.skirmish_report.WarriorGrowthRecorded": _RECORD_WRITTEN,
    "apps.warband.skirmish.messages.events.warrior.LastUsedSkirmishActionStored": (
        "A default for the next round's order form, read off the warrior when the fight page renders."
    ),
    "apps.warband.training.messages.events.training.NewTrainingCreated": (
        "A new faction's regimen, read off its row when the training page renders. Nothing else holds a copy "
        "that would need telling."
    ),
}


# Command handlers allowed to emit commands, against the golden rule in
# "docs/patterns/message-bus.md". One entry, and an addition wants the reason written next to it.
#
# "handle_assign_fighter_pairs" decomposes one order into several and writes nothing itself. The orders it
# issues are late-bound by design - "handle_warrior_withdraws_from_skirmish" re-checks the man when the
# command drains, because a warrior ordered to flee can be routed by a comrade falling first - so an event
# at this point would announce a departure that may never happen.
DIRECTION_ALLOWLIST: frozenset[str] = frozenset(
    {
        "apps.warband.skirmish.handlers.commands.skirmish.handle_assign_fighter_pairs",
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

    assert emitted_events - set(queuebie_registry.event_dict) - set(TERMINAL_MESSAGES) == set()


def test_every_terminal_message_carries_a_reason():
    entries_without_a_reason = sorted(path for path, reason in TERMINAL_MESSAGES.items() if not reason.strip())

    assert entries_without_a_reason == []


def test_every_terminal_message_is_still_emitted_and_still_unconsumed(queuebie_registry):
    """
    A stale entry is invisible otherwise. An event that gained a consumer, or stopped being raised at all,
    keeps its place on the list - and the reason beside it goes on explaining a silence that is no longer
    there.
    """
    emitted_events = _emitted_message_paths(message_type=Event)
    stale_entries = sorted(
        path for path in TERMINAL_MESSAGES if path not in emitted_events or path in queuebie_registry.event_dict
    )

    assert stale_entries == []


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


def _topic_of(*, module_path: str) -> str:
    # "apps.warband.<topic>.…"
    return module_path.split(".")[2]


def _event_module_mismatches(*, registry) -> list[str]:
    """
    Every "handlers/events/" module that reacts to one foreign topic only and is not named after it.

    The two fallbacks from "docs/patterns/app-layout.md" are left alone because they name a subject, and a
    subject is a judgement call this cannot check: a module reacting to its own topic's events, and one
    reacting to several topics.
    """
    origins_by_module: dict[str, set[str]] = {}

    for event_path, handler_list in registry.event_dict.items():
        for definition in handler_list:
            origins_by_module.setdefault(definition["module"], set()).add(_topic_of(module_path=event_path))

    mismatches = []
    for module_path, origins in sorted(origins_by_module.items()):
        module_name = module_path.rsplit(".", 1)[-1]
        if len(origins) != 1 or _topic_of(module_path=module_path) in origins:
            continue

        (origin,) = origins
        if module_name != origin:
            mismatches.append(f"{module_path} only reacts to {origin} events but is named {module_name!r}")

    return mismatches


def test_event_module_mismatches_names_a_module_reacting_to_one_foreign_topic_under_another_name():
    registry = types.SimpleNamespace(
        event_dict={
            "apps.warband.skirmish.messages.events.skirmish.SkirmishFinished": [
                {"module": "apps.warband.finance.handlers.events.quest_contract", "name": "handler"},
                {"module": "apps.warband.finance.handlers.events.skirmish", "name": "handler"},
            ],
        }
    )

    result = _event_module_mismatches(registry=registry)

    assert result == [
        "apps.warband.finance.handlers.events.quest_contract only reacts to skirmish events but is named "
        "'quest_contract'"
    ]


def test_event_module_mismatches_leaves_the_two_subject_fallbacks_alone():
    """
    A topic reacting to its own events, and a module reacting to several topics, both name a subject.
    """
    registry = types.SimpleNamespace(
        event_dict={
            "apps.warband.skirmish.messages.events.skirmish.SkirmishFinished": [
                {"module": "apps.warband.skirmish.handlers.events.warrior", "name": "handler"},
                {"module": "apps.warband.faction.handlers.events.item", "name": "handler"},
            ],
            "apps.warband.month.messages.events.month.MonthPrepared": [
                {"module": "apps.warband.faction.handlers.events.item", "name": "handler"},
            ],
        }
    )

    result = _event_module_mismatches(registry=registry)

    assert result == []


def test_an_event_handler_module_is_named_after_the_topic_it_reacts_to(queuebie_registry):
    """
    The other half of the test above. Under "handlers/events/" the topic package is the reactor, so the
    module name is what carries the origin - which is what makes a cross-topic subscription findable at
    all. A module named after a subject instead wires up and runs exactly the same.
    """
    mismatches = _event_module_mismatches(registry=queuebie_registry)

    assert mismatches == []


def _emitted_message_types(
    *,
    node: ast.FunctionDef,
    module,
    local_nodes: dict[str, ast.FunctionDef],
    handler_nodes: dict[tuple[str, str], ast.FunctionDef] | None = None,
) -> set[type]:
    """
    Every message class a handler puts into the queue, the helpers it delegates to included.

    Following those calls is what makes this see "handle_assign_fighter_pairs": it instantiates no
    command itself, "_withdrawing_and_remaining" does. A walk of the decorated function alone misses
    the one handler the golden rule is bent for.

    Two kinds of delegation are followed. A bare name defined in the handler's own module is taken
    from "local_nodes". Anything else is resolved against the module's namespace, and followed when it
    turns out to be a function living in one of the other handler modules - which covers a handler
    calling a helper it imported from a sibling handler module, spelled either way round.

    **What it cannot see: a message constructed in a module that holds no handlers**, a "services/"
    helper being the obvious candidate. That blind spot is the whole file's rather than this
    function's - "_emitted_message_paths" reads the same set of files, so test 2 cannot see such a
    command either - and closing it means resolving imports across the tree. Nothing in the project
    builds a message outside a handler or a view today.
    """
    emitted = set()
    visited: set[tuple[str, str]] = set()

    def collect(*, current: ast.FunctionDef, current_module) -> None:
        for child in ast.walk(current):
            if not isinstance(child, ast.Call):
                continue

            resolved = _resolve(node=child.func, module=current_module)

            if isinstance(resolved, type) and issubclass(resolved, (Command, Event)):
                emitted.add(resolved)
                continue

            # A bare name defined beside the handler. Recursion guarded, so a helper calling itself
            # does not walk for ever.
            if isinstance(child.func, ast.Name) and child.func.id in local_nodes:
                key = (getattr(current_module, "__name__", ""), child.func.id)
                if key not in visited:
                    visited.add(key)
                    collect(current=local_nodes[child.func.id], current_module=current_module)
                continue

            # A function reached through an import, followed only as far as the handler modules go
            if handler_nodes is None or not isinstance(resolved, types.FunctionType):
                continue

            key = (resolved.__module__, resolved.__name__)
            if key in handler_nodes and key not in visited:
                visited.add(key)
                collect(current=handler_nodes[key], current_module=importlib.import_module(resolved.__module__))

    collect(current=node, current_module=module)

    return emitted


def _wrong_direction_emissions(*, registry, allowlist: frozenset[str] = DIRECTION_ALLOWLIST) -> list[str]:
    """
    Every handler emitting the message type its own kind is not allowed to emit.

    The allowlist is an argument so the test below it can ask the same question with the exemptions
    lifted, which is the only way a stale entry becomes visible.
    """
    handler_nodes = _handler_nodes()
    violations = set()

    for message_dict, forbidden_type, expected in (
        (registry.command_dict, Command, "events"),
        (registry.event_dict, Event, "commands"),
    ):
        for handler_list in message_dict.values():
            for definition in handler_list:
                handler_path = f"{definition['module']}.{definition['name']}"
                if handler_path in allowlist:
                    continue

                emitted = _emitted_message_types(
                    node=handler_nodes[(definition["module"], definition["name"])],
                    module=importlib.import_module(definition["module"]),
                    local_nodes={
                        name: node
                        for (module_path, name), node in handler_nodes.items()
                        if module_path == definition["module"]
                    },
                    handler_nodes=handler_nodes,
                )

                for message_class in emitted:
                    if issubclass(message_class, forbidden_type):
                        violations.add(
                            f"{handler_path} emits {message_class.module_path()}, "
                            f"but a handler of this kind emits {expected}"
                        )

    return sorted(violations)


def _emitted_types_in(*, source: str, namespace: dict) -> set[type]:
    """
    Runs the collector over a source snippet, for the tests of the collector itself.
    """
    tree = ast.parse(source)
    local_nodes = {node.name: node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}

    return _emitted_message_types(
        node=local_nodes["handler"],
        module=types.SimpleNamespace(**namespace),
        local_nodes=local_nodes,
    )


def test_emitted_message_types_names_the_event_a_conforming_command_handler_emits():
    source = "def handler(*, context):\n    return WarriorMonthPrepared(faction=1, warrior=2, month=3)\n"

    result = _emitted_types_in(source=source, namespace={"WarriorMonthPrepared": WarriorMonthPrepared})

    assert result == {WarriorMonthPrepared}


def test_emitted_message_types_names_the_command_a_command_handler_emits():
    source = "def handler(*, context):\n    return HealInjuredWarrior(faction=1, warrior=2, month=3)\n"

    result = _emitted_types_in(source=source, namespace={"HealInjuredWarrior": HealInjuredWarrior})

    assert result == {HealInjuredWarrior}


def test_emitted_message_types_follows_a_module_local_helper():
    """
    The "handle_assign_fighter_pairs" shape: the handler instantiates nothing itself, a helper beside
    it does. Without this the one handler the allowlist exists for is the one the test cannot see.
    """
    source = (
        "def build():\n"
        "    return HealInjuredWarrior(faction=1, warrior=2, month=3)\n"
        "\n"
        "def handler(*, context):\n"
        "    return build()\n"
    )

    result = _emitted_types_in(source=source, namespace={"HealInjuredWarrior": HealInjuredWarrior})

    assert result == {HealInjuredWarrior}


def test_emitted_message_types_follows_a_helper_imported_from_another_handler_module():
    """
    The near miss a module-local walk alone would wave through: a handler emitting through a helper it
    imported rather than one defined beside it.

    "_withdrawing_and_remaining" stands in for that helper, and is the honest choice for it - a real
    undecorated function in a real handler module which really does build a command, reached here by
    an imported name. Finding the WithdrawFromSkirmish inside it is proof the walk crossed the module
    boundary, because nothing in the snippet mentions that command.
    """
    source = "def handler(*, context):\n    return _withdrawing_and_remaining()\n"
    tree = ast.parse(source)

    result = _emitted_message_types(
        node={node.name: node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}["handler"],
        module=types.SimpleNamespace(__name__="stand_in", _withdrawing_and_remaining=_withdrawing_and_remaining),
        local_nodes={},
        handler_nodes=_handler_nodes(),
    )

    assert result == {WithdrawFromSkirmish}


def test_emitted_message_types_survives_a_helper_calling_itself():
    source = (
        "def build(depth):\n"
        "    if depth:\n"
        "        return build(depth - 1)\n"
        "    return HealInjuredWarrior(faction=1, warrior=2, month=3)\n"
        "\n"
        "def handler(*, context):\n"
        "    return build(2)\n"
    )

    result = _emitted_types_in(source=source, namespace={"HealInjuredWarrior": HealInjuredWarrior})

    assert result == {HealInjuredWarrior}


def test_a_command_handler_emits_events_and_an_event_handler_emits_commands(queuebie_registry):
    """
    The golden rule of "docs/patterns/message-bus.md", which nothing else in the project enforces.

    Strict mode checks a command handler's scope at registration and wraps event handlers in a
    database blocker at dispatch; neither looks at the direction of a hop. So a command handler
    emitting commands wires up, runs, and reads exactly like the handler above it - which is how four
    of them came to do it, one of them written up in the docs as the intended shape.

    Parsed out of the syntax tree rather than off the return annotations: every handler in this project
    annotates abstractly, and an annotation can lie while the code cannot. The failure this guards
    against is somebody copying the handler above them, annotation included.
    """
    violations = _wrong_direction_emissions(registry=queuebie_registry)

    assert violations == []


def test_every_allowlisted_handler_still_emits_the_message_type_it_was_allowed(queuebie_registry):
    """
    A stale allowlist entry is invisible otherwise: the handler it names keeps being skipped after the
    reason for skipping it is gone, and the next handler in that module inherits the exemption by
    sitting next to it.
    """
    violations_without_exemptions = " ".join(
        _wrong_direction_emissions(registry=queuebie_registry, allowlist=frozenset())
    )
    entries_no_longer_needed = sorted(
        handler_path for handler_path in DIRECTION_ALLOWLIST if handler_path not in violations_without_exemptions
    )

    assert entries_no_longer_needed == []


def _message_classes() -> list[type]:
    """
    Every command and event defined in a "messages/" module, whether or not anything handles it yet.
    """
    message_classes = []
    for file in production_module_files():
        if "messages" not in file.parts:
            continue
        module = importlib.import_module(module_path_for(file=file))
        message_classes.extend(
            member
            for member in vars(module).values()
            if isinstance(member, type)
            and issubclass(member, (Command, Event))
            and member not in (Command, Event)
            and member.__module__ == module.__name__
        )

    return message_classes


def _names_a_queryset(*, annotation: object) -> bool:
    # An annotation naming a type only imported for type checking stays unresolved, so the name is all
    # there is to go on
    if isinstance(annotation, str | ForwardRef):
        return "QuerySet" in str(annotation)
    if isinstance(annotation, type) and issubclass(annotation, QuerySet):
        return True

    origin = typing.get_origin(annotation)
    if isinstance(origin, type) and issubclass(origin, QuerySet):
        return True

    return any(_names_a_queryset(annotation=argument) for argument in typing.get_args(annotation))


def _queryset_fields(*, message_classes: list[type]) -> list[str]:
    return sorted(
        f"{message_class.__module__}.{message_class.__name__}.{field.name}"
        for message_class in message_classes
        if dataclasses.is_dataclass(message_class)
        for field in dataclasses.fields(message_class)
        if _names_a_queryset(annotation=field.type)
    )


def test_queryset_fields_names_every_way_of_spelling_a_queryset():
    @dataclasses.dataclass(kw_only=True)
    class Spelled(Event):
        bare: QuerySet
        generic: QuerySet[Warrior]
        union: QuerySet[Warrior] | list[Warrior]
        nested: list[QuerySet[Warrior]]
        forward: QuerySet[Warrior]
        fine: list[Warrior]

    assert _queryset_fields(message_classes=[Spelled]) == [
        f"{__name__}.Spelled.{name}" for name in ("bare", "forward", "generic", "nested", "union")
    ]


def test_no_message_carries_a_queryset():
    """
    A queryset on a message is a query waiting for whoever touches it first, and strict mode forbids
    one in every event handler. Messages carry lists - see "docs/patterns/message-bus.md".
    """
    assert _queryset_fields(message_classes=_message_classes()) == []
