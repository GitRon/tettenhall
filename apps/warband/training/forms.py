from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, Div, Field, Layout, Submit
from django import forms

from apps.common import form_styles
from apps.warband.training.models.training import Training


def build_training_category_help_text() -> str:
    """
    Say which attribute each category grows, read off the mapping the month itself rolls from.

    The three category names are the game's own vocabulary and name no attribute between them, so the
    choice was made against an overview whose columns are Strength, Dexterity, Health and Morale with
    nothing connecting the two. Built rather than written out, so a category that starts growing
    something else says so here without anybody remembering to come back.
    """
    return " ".join(
        f"{label} grows {Training.attributes_display_for_category(category=value)}."
        for value, label in Training.TrainingCategory.choices
    )


class TrainingForm(forms.ModelForm):
    class Meta:
        model = Training
        fields = ("category",)

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.layout = Layout(
            Div(Field("category", css_class=form_styles.SELECT)),
            Div(
                Submit(
                    "submit",
                    "Save",
                    css_class=form_styles.BUTTON_PRIMARY_SMALL,
                ),
                # The only way off this page otherwise is the navbar, which leaves the player on a
                # form they have already changed with no way to abandon it.
                HTML(
                    "<a href=\"{% url 'warband:dashboard-view' %}\""
                    f' class="{form_styles.BUTTON_DEFAULT_SMALL}">Cancel</a>'
                ),
            ),
        )

        super().__init__(*args, **kwargs)

        self.fields["category"].help_text = build_training_category_help_text()
