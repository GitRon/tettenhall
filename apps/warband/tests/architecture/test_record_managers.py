"""
Architectural test for the name of the manager method that writes a record.

"docs/patterns/app-layout.md" settles that a record of something that happened is written through
"Model.objects.create_record()", whatever the model. A manager inventing a name of its own works exactly
the same, and "where is a row of this written" then has one answer per model to remember rather than one
for the project - so it is checked here, over the manager sources, for every manager at once.
"""

import ast

from apps.warband.tests.architecture.discovery import production_module_files

# The manager calls that write a row
ROW_WRITING_METHODS = frozenset({"create", "get_or_create", "update_or_create", "bulk_create"})

RECORD_METHOD_NAME = "create_record"


def _writes_a_row(*, method: ast.FunctionDef) -> bool:
    return any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr in ROW_WRITING_METHODS
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "self"
        for node in ast.walk(method)
    )


def _misnamed_record_writers(*, tree: ast.AST) -> list[str]:
    """
    Every method of a class writing a row through its own manager under a name other than "create_record".
    """
    return [
        f"{class_node.name}.{method.name}"
        for class_node in ast.walk(tree)
        if isinstance(class_node, ast.ClassDef)
        for method in class_node.body
        if isinstance(method, ast.FunctionDef) and method.name != RECORD_METHOD_NAME and _writes_a_row(method=method)
    ]


def test_misnamed_record_writers_names_a_method_writing_a_row_under_another_name():
    source = (
        "class CasualtyManager:\n"
        "    def record_casualty(self, *, fate):\n"
        "        return self.update_or_create(fate=fate)\n"
        "\n"
        "    def create_record(self, *, fate):\n"
        "        return self.create(fate=fate)\n"
        "\n"
        "    def reduce(self, *, obj):\n"
        "        return self.filter(id=obj.id).update(fate=0)\n"
    )

    result = _misnamed_record_writers(tree=ast.parse(source))

    assert result == ["CasualtyManager.record_casualty"]


def test_a_manager_writes_a_record_through_create_record():
    violations = [
        f"{file.relative_to(file.parents[3])} {violation}"
        for file in production_module_files()
        if "managers" in file.parts
        for violation in _misnamed_record_writers(tree=ast.parse(file.read_text(encoding="utf-8")))
    ]

    assert violations == []
