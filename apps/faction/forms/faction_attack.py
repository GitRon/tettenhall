from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Field, Layout, Submit
from django import forms

from apps.skirmish.models.warrior import Warrior


class FactionAttackForm(forms.Form):
    """
    Picks the war band the player marches with.

    The leader is deliberately not one of the choices: the story has him joining every attack, and a
    checkbox he could clear would be a promise the form cannot keep. He is added back in
    "get_assigned_warriors()" instead, so no posted value can leave him at home.
    """

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
            Div(Field("assigned_warriors", css_class="uk-select")),
            Div(
                Submit(
                    "submit",
                    "Attack",
                    css_class="uk-button uk-button-danger uk-button-small",
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

    def get_assigned_warriors(self) -> list[Warrior]:
        """
        The war band that marches: whoever the player picked, plus the leader he cannot leave behind.
        """
        return [self.leader, *self.cleaned_data["assigned_warriors"]]
