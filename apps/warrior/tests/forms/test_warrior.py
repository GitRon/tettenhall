import pytest

from apps.skirmish.tests.factories.warrior import WarriorFactory
from apps.warrior.forms.warrior import WarriorForm


def test_init_rejects_a_field_the_form_does_not_render():
    """
    Unreachable through the view, which validates the attribute from the URL first, so the guard
    gets tested on the form directly.
    """
    with pytest.raises(RuntimeError, match="Badly configured HTMX form"):
        WarriorForm(instance=WarriorFactory.build(), htmx_field="nickname")
