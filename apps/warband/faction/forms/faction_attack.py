from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Field, Layout, Submit
from django import forms

from apps.common import form_styles
from apps.warband.skirmish.models.warrior import Warrior


class FactionAttackForm(forms.Form):
    """
    Picks the war band the player marches with.

    The leader is deliberately not one of the choices: the story has him joining every attack, and a
    checkbox he could clear would be a promise the form cannot keep. He is added back in
    "get_assigned_warriors()" instead, so no posted value can leave him at home.
    """

    # Why the picker is empty, said in the field's own help text. A "<select multiple>" with no
    # options in it reads as a broken page, and which of the three rules emptied it is the only part
    # the player can do anything about.
    EMPTY_NO_OTHERS = "You have nobody else on the roster."
    EMPTY_NONE_ABLE = "Your other warriors are in no condition to march."
    EMPTY_ALL_COMMITTED = "Your other warriors are already committed this month."
    EMPTY_TAIL = "Your leader marches alone."

    assigned_warriors = forms.ModelMultipleChoiceField(
        queryset=Warrior.objects.none(),
        label="Assigned warriors",
        # The leader marches on his own if it comes to it - a lone attack is a bad idea, not an
        # invalid one
        required=False,
    )

    def __init__(self, *args, **kwargs):
        self.leader = kwargs.pop("leader")
        self.month = kwargs.pop("month")

        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.layout = Layout(
            Div(Field("assigned_warriors", css_class=form_styles.SELECT_MULTIPLE)),
            Div(
                Submit(
                    "submit",
                    "Attack",
                    css_class=form_styles.BUTTON_DANGER_SMALL,
                )
            ),
        )

        # The queryset is what validates here: left at the default, a hand-edited id would send
        # another faction's warrior - or a wounded one - into the fight
        self.fields["assigned_warriors"].queryset = (
            Warrior.objects.filter_healthy()
            .filter_faction(faction_id=self.leader.faction_id)
            .exclude_currently_busy(month=self.month)
            .exclude(id=self.leader.id)
            .distinct()
        )

        if not self.fields["assigned_warriors"].queryset.exists():
            self.fields["assigned_warriors"].help_text = self._get_empty_help_text()

    def _get_empty_help_text(self) -> str:
        """
        Which of the three rules left the picker with nothing in it.

        Asked only once the field is known to be empty, so the ordinary path pays a single
        "exists()" and the two queries below are the price of a sentence nobody else can supply.
        """
        others = Warrior.objects.filter_faction(faction_id=self.leader.faction_id).exclude(id=self.leader.id)

        if not others.exists():
            reason = self.EMPTY_NO_OTHERS
        elif not others.filter_healthy().exists():
            reason = self.EMPTY_NONE_ABLE
        else:
            reason = self.EMPTY_ALL_COMMITTED

        return f"{reason} {self.EMPTY_TAIL}"

    def get_assigned_warriors(self) -> list[Warrior]:
        """
        The war band that marches: whoever the player picked, plus the leader he cannot leave behind.
        """
        return [self.leader, *self.cleaned_data["assigned_warriors"]]
