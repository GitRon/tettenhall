from django.forms.models import ModelChoiceIteratorValue

from apps.warband.warrior.forms.widgets import RosterCheckboxSelectMultiple


def test_create_option_greys_out_a_man_who_cannot_go():
    widget = RosterCheckboxSelectMultiple(reasons_by_warrior_id={7: "Unconscious"})

    result = widget.create_option(
        "assigned_warriors", ModelChoiceIteratorValue(7, None), "Osric", selected=False, index=0
    )

    assert result["attrs"]["disabled"] is True
    assert result["reason"] == "Unconscious"


def test_create_option_leaves_a_man_who_can_go_pickable():
    widget = RosterCheckboxSelectMultiple(reasons_by_warrior_id={7: "Unconscious"})

    result = widget.create_option(
        "assigned_warriors", ModelChoiceIteratorValue(8, None), "Eadric", selected=False, index=1
    )

    assert "disabled" not in result["attrs"]
    assert result["reason"] is None


def test_create_option_of_a_value_that_wraps_no_warrior():
    """
    A blank choice arrives as a plain empty string rather than as a "ModelChoiceIteratorValue", so
    the unwrapping has to survive one.
    """
    widget = RosterCheckboxSelectMultiple(reasons_by_warrior_id={7: "Unconscious"})

    result = widget.create_option("assigned_warriors", "", "", selected=False, index=0)

    assert result["reason"] is None
