from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Field, Layout, Submit
from django import forms
from django.db.models import QuerySet

from apps.common import form_styles
from apps.warband.skirmish.models.warrior import Warrior
from apps.warband.warrior.forms.widgets import RosterCheckboxSelectMultiple
from apps.warband.warrior.services.availability import assess_roster


class FactionAttackForm(forms.Form):
    """
    Picks the war band the player marches with.

    The leader is deliberately not one of the choices: the story has him joining every attack, and a
    checkbox he could clear would be a promise the form cannot keep. He is added back in
    "get_assigned_warriors()" instead, so no posted value can leave him at home.
    """

    ROSTER_FIELD_TEMPLATE = "warrior/components/roster_picker_field.html"

    # The one state that draws no rows at all, and so the one the field still has to put into words.
    # Which rule is keeping each of the others at home is said on his own row now - see
    # [assess_roster], which is where that vocabulary lives for both forms that need it.
    EMPTY_NO_OTHERS = "You have nobody else on the roster."
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
            Div(Field("assigned_warriors", template=self.ROSTER_FIELD_TEMPLATE)),
            Div(
                Submit(
                    "submit",
                    "Attack",
                    css_class=form_styles.BUTTON_DANGER_SMALL,
                )
            ),
        )

        # The whole war band bar the leader, each man with a verdict. He is excluded rather than
        # greyed out with a reason, because "he is coming regardless" is not a reason he cannot go -
        # the template says so beside the field instead.
        self.roster = assess_roster(
            faction_id=self.leader.faction_id,
            month=self.month,
            excluded_ids=(self.leader.id,),
        )

        # Widget first, then queryset: assigning a queryset is what hands a field's choices to the
        # widget it is holding at that moment.
        self.fields["assigned_warriors"].widget = RosterCheckboxSelectMultiple(
            reasons_by_warrior_id=self.roster.reasons_by_warrior_id
        )
        # Everybody, because an option missing from the queryset is an option that does not render.
        # The scoping it still performs is the faction one, so a hand-edited id cannot march a
        # rival's warrior out under the player's banner; who may be picked is checked below.
        self.fields["assigned_warriors"].queryset = self.roster.as_queryset()

        if self.roster.is_empty:
            self.fields["assigned_warriors"].help_text = f"{self.EMPTY_NO_OTHERS} {self.EMPTY_TAIL}"

    def clean_assigned_warriors(self) -> QuerySet[Warrior]:
        """
        Refuse a man the roster marked unavailable.

        The queryset cannot do this any more: it has to hold the men who cannot march so the page can
        draw them. "disabled" keeps the browser from submitting those boxes and does nothing about a
        hand-edited post, so the rule is performed here - against the same assessment the page was
        drawn from, rather than against a second query that could answer differently.
        """
        assigned_warriors = self.cleaned_data["assigned_warriors"]

        unavailable = [warrior for warrior in assigned_warriors if warrior.id not in self.roster.available_ids]
        if unavailable:
            raise forms.ValidationError(
                "%(names)s cannot march this month.",
                params={"names": ", ".join(warrior.name for warrior in unavailable)},
            )

        return assigned_warriors

    def get_assigned_warriors(self) -> list[Warrior]:
        """
        The war band that marches: whoever the player picked, plus the leader he cannot leave behind.
        """
        return [self.leader, *self.cleaned_data["assigned_warriors"]]
