from django import forms


class RosterCheckboxSelectMultiple(forms.CheckboxSelectMultiple):
    """
    A war band drawn in full: one checkbox per man, and beside the ones who cannot go, why.

    A "<select multiple>" can only leave a man out. It has no room for a sentence per option and no
    portrait form worth the name, which is the pair of reasons this is a list of checkboxes instead.

    The "disabled" attribute is a courtesy to the browser, which then declines to submit the box. It
    is not the rule: a hand-edited post carries whatever it likes, and the forms using this widget
    check every posted id against the assessment themselves.
    """

    def __init__(self, *args, reasons_by_warrior_id: dict[int, str] | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.reasons_by_warrior_id = reasons_by_warrior_id or {}

    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None) -> dict:  # noqa: PBR001
        """
        Hang the verdict on the option, so the field template can draw it next to the man.

        The value arriving here is a "ModelChoiceIteratorValue" rather than the primary key it wraps,
        and it is a plain empty string for a blank choice - hence the unwrapping before the lookup.
        """
        option = super().create_option(name, value, label, selected, index, subindex=subindex, attrs=attrs)

        reason = self.reasons_by_warrior_id.get(getattr(value, "value", None))
        if reason is not None:
            option["attrs"]["disabled"] = True
        option["reason"] = reason

        return option
