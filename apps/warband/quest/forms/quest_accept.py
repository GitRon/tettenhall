from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Field, Layout, Submit
from django import forms
from django.db.models import QuerySet

from apps.common import form_styles
from apps.warband.faction.models import Faction
from apps.warband.quest.models.quest import Quest
from apps.warband.quest.models.quest_contract import QuestContract
from apps.warband.skirmish.models.warrior import Warrior
from apps.warband.warrior.forms.widgets import RosterCheckboxSelectMultiple
from apps.warband.warrior.services.availability import assess_roster


class QuestAcceptForm(forms.ModelForm):
    ROSTER_FIELD_TEMPLATE = "warrior/components/roster_picker_field.html"

    #: Said under the picker when every row in it is greyed. The rows carry the reasons themselves,
    #: so this only has to name the shape of the situation rather than explain it.
    NOBODY_AVAILABLE = "None of your men can take a quest this month."

    class Meta:
        model = QuestContract
        fields = ("faction", "quest", "assigned_warriors")

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.layout = Layout(
            Div(Field("faction"), Field("quest")),
            Div(Field("assigned_warriors", template=self.ROSTER_FIELD_TEMPLATE)),
            Div(
                Submit(
                    "submit",
                    "Accept quest",
                    css_class=form_styles.BUTTON_PRIMARY_SMALL,
                )
            ),
        )

        quest_id = kwargs.pop("quest_id")
        player_faction_id = kwargs.pop("player_faction_id")

        super().__init__(*args, **kwargs)

        # Both fields are hidden inputs, so their querysets have to do the validating: left at the
        # default "everything" a hand-edited value would name another player's quest or faction
        quest_qs = Quest.objects.filter(id=quest_id)
        quest = quest_qs.first()
        self.fields["quest"].queryset = quest_qs
        self.fields["quest"].initial = quest
        self.fields["quest"].widget = forms.HiddenInput()

        faction_qs = Faction.objects.filter(id=player_faction_id)
        faction = faction_qs.get()
        self.fields["faction"].queryset = faction_qs
        self.fields["faction"].initial = faction
        self.fields["faction"].widget = forms.HiddenInput()

        # The whole war band, each man with a verdict - not just the men who can go. A picker that
        # silently dropped the other four rendered a shorter roster than the one the player owns and
        # left him to work out the difference, which reads as a broken page rather than as a rule.
        self.roster = assess_roster(
            faction_id=faction.id,
            month=quest.target_faction.savegame.current_month,
        )

        # The widget before the queryset, not after: assigning a queryset is what hands a field's
        # choices to whatever widget it is holding at that moment, so a widget swapped in afterwards
        # renders no options at all.
        self.fields["assigned_warriors"].widget = RosterCheckboxSelectMultiple(
            reasons_by_warrior_id=self.roster.reasons_by_warrior_id
        )
        # The queryset holds everybody, because an option that is not in it is an option that does
        # not render. What it still does is scope to this faction, so no posted id can reach a
        # rival's man; which of this faction's men may be picked is "clean_assigned_warriors".
        self.fields["assigned_warriors"].queryset = self.roster.as_queryset()

        if self.roster.has_nobody_available:
            self.fields["assigned_warriors"].help_text = self.NOBODY_AVAILABLE

    def clean_assigned_warriors(self) -> QuerySet[Warrior]:
        """
        Refuse a man the roster marked unavailable.

        The queryset used to be what enforced this, and it cannot be any more: it has to hold the men
        who cannot go so that the page can draw them. The "disabled" attribute stops the browser
        submitting those boxes and stops nothing else, so the rule is performed here - against the
        very assessment the page was drawn from, rather than against a second query that could
        disagree with it.
        """
        assigned_warriors = self.cleaned_data["assigned_warriors"]

        unavailable = [warrior for warrior in assigned_warriors if warrior.id not in self.roster.available_ids]
        if unavailable:
            raise forms.ValidationError(
                "%(names)s cannot take a quest this month.",
                params={"names": ", ".join(warrior.name for warrior in unavailable)},
            )

        return assigned_warriors
