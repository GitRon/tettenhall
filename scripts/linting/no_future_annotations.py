import ast

from boa_restrictor.common.rule import Rule
from boa_restrictor.projections.occurrence import Occurrence

TETTENHALL_LINTING_RULE_PREFIX = "TBR"


class NoFutureAnnotationsImportRule(Rule):
    """
    Prohibits "from __future__ import annotations".

    PEP 649 landed in Python 3.14 and makes annotations lazy on its own, which is the one thing the
    import bought. On the Python this project requires it does nothing: an unquoted forward reference
    to a class defined further down the file resolves without it. What it still costs is a reader
    concluding that the file has a forward-reference problem someone had to solve.
    """

    RULE_ID = f"{TETTENHALL_LINTING_RULE_PREFIX}001"
    RULE_LABEL = 'Prohibiting "from __future__ import annotations", which PEP 649 makes redundant.'

    def check(self) -> list[Occurrence]:
        occurrences = []

        for node in ast.walk(self.source_tree):
            if isinstance(node, ast.ImportFrom) and node.module == "__future__":
                for alias in node.names:
                    if alias.name == "annotations":
                        occurrences.append(self._build_occurrence(line_number=node.lineno))

        return occurrences
