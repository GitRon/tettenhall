from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Field, Layout, Submit
from django import forms

from apps.training.models.training import Training


class TrainingForm(forms.ModelForm):
    class Meta:
        model = Training
        fields = ("category",)

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.layout = Layout(
            Div(Field("category", css_class="uk-select")),
            Div(
                Submit(
                    "submit",
                    "Save",
                    css_class="uk-button uk-button-primary uk-button-small",
                )
            ),
        )

        super().__init__(*args, **kwargs)
