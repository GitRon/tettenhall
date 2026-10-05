from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Field, Layout, Submit
from django import forms
from django.db.models import QuerySet

from apps.common import form_styles
from apps.warband.quest.models.quest import Quest
from apps.warband.quest.quests import QUESTS_BY_NAME
from apps.warband.skirmish.models.warrior import Warrior
from apps.warband.warrior.forms.fields import WarriorMultipleChoiceField
from apps.warband.warrior.forms.widgets import RosterCheckboxSelectMultiple
from apps.warband.warrior.services.availability import assess_roster


class QuestAcceptForm(forms.Form):
    ROSTER_FIELD_TEMPLATE = "warrior/components/roster_picker_field.html"

    #: Said under the picker when every row in it is greyed. The rows carry the reasons themselves,
    #: so this only has to name the shape of the situation rather than explain it.
    NOBODY_AVAILABLE = "None of your men can be sent on a quest this month."

    # Each man offered by his full name, so the player can see who he is sending
    assigned_warriors = WarriorMultipleChoiceField(queryset=Warrior.objects.none(), label="Men to send")

    def __init__(self, *args, quest: Quest, month: int, **kwargs):
        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.layout = Layout(
            Div(Field("assigned_warriors", template=self.ROSTER_FIELD_TEMPLATE)),
            Div(Submit("submit", "Send them", css_class=form_styles.BUTTON_PRIMARY_SMALL)),
        )

        super().__init__(*args, **kwargs)

        self.entry = QUESTS_BY_NAME[quest.quest]

        # The whole war band, each man with a verdict - not just the men who can go. A picker that
        # silently dropped the others rendered a shorter roster than the one the player owns and left
        # him to work out the difference, which reads as a broken page rather than as a rule.
        self.roster = assess_roster(faction_id=quest.faction_id, month=month)

        # The widget before the queryset, not after: assigning a queryset is what hands a field's
        # choices to whatever widget it is holding at that moment, so a widget swapped in afterwards
        # renders no options at all.
        # Each man with the attribute the quest weighs the band on, so the player can see who makes it
        # likelier to go well while he chooses
        self.fields["assigned_warriors"].widget = RosterCheckboxSelectMultiple(
            reasons_by_warrior_id=self.roster.reasons_by_warrior_id,
            figure_label=Warrior._meta.get_field(self.entry.LEANS_ON).verbose_name,
            figures_by_warrior_id={
                assessment.warrior.id: getattr(assessment.warrior, self.entry.LEANS_ON)
                for assessment in self.roster.assessed
            },
        )
        # The queryset holds everybody, because an option that is not in it is an option that does
        # not render. What it still does is scope to this faction, so no posted id can reach a
        # rival's man; which of this faction's men may be picked is "clean_assigned_warriors".
        self.fields["assigned_warriors"].queryset = self.roster.as_queryset()

        if self.roster.has_nobody_available:
            self.fields["assigned_warriors"].help_text = self.NOBODY_AVAILABLE

    def clean_assigned_warriors(self) -> QuerySet[Warrior]:
        """
        Refuse a man the roster marked unavailable, and a band the quest does not take.

        The availability is checked against the very assessment the page was drawn from, because the
        "disabled" attribute stops the browser submitting a greyed box and stops nothing else.
        """
        assigned_warriors = self.cleaned_data["assigned_warriors"]

        unavailable = [warrior for warrior in assigned_warriors if warrior.id not in self.roster.available_ids]
        if unavailable:
            raise forms.ValidationError(
                "%(names)s cannot be sent on a quest this month.",
                params={"names": ", ".join(warrior.display_name for warrior in unavailable)},
            )

        if not self.entry.MIN_MEN <= len(assigned_warriors) <= self.entry.MAX_MEN:
            raise forms.ValidationError(
                "This quest takes %(minimum)s to %(maximum)s men.",
                params={"minimum": self.entry.MIN_MEN, "maximum": self.entry.MAX_MEN},
            )

        return assigned_warriors
