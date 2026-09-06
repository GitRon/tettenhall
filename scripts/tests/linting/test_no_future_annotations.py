import ast
from pathlib import Path

from boa_restrictor.projections.occurrence import Occurrence

from scripts.linting.no_future_annotations import NoFutureAnnotationsImportRule


def test_check_flags_the_annotations_import():
    source_tree = ast.parse("from __future__ import annotations\n\nfrom dataclasses import dataclass\n")

    occurrence_list = NoFutureAnnotationsImportRule.run_check(
        file_path=Path("skirmish_report.py"), source_tree=source_tree
    )

    assert occurrence_list == [
        Occurrence(
            rule_id="TBR001",
            rule_label=NoFutureAnnotationsImportRule.RULE_LABEL,
            filename="skirmish_report.py",
            file_path=Path("skirmish_report.py"),
            identifier=None,
            line_number=1,
        )
    ]


def test_check_leaves_other_future_imports_alone():
    source_tree = ast.parse("from __future__ import division\n")

    occurrence_list = NoFutureAnnotationsImportRule.run_check(
        file_path=Path("skirmish_report.py"), source_tree=source_tree
    )

    assert occurrence_list == []


def test_check_passes_a_file_without_the_import():
    source_tree = ast.parse("import ast\n\nfrom dataclasses import dataclass\n\n\ndef parse():\n    return ast\n")

    occurrence_list = NoFutureAnnotationsImportRule.run_check(
        file_path=Path("skirmish_report.py"), source_tree=source_tree
    )

    assert occurrence_list == []
