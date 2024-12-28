from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Field, Fieldset, Layout, Submit
from django import forms
from django.contrib.auth import authenticate, user_login_failed
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist


class LoginForm(forms.Form):
    user_cache: User = None

    email = forms.CharField(label="Email address", max_length=120)
    password = forms.CharField(label="Password", widget=forms.PasswordInput)

    def __init__(self, request=None, *args, **kwargs):  # noqa: PBR001
        self.request = request

        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.layout = Layout(
            Fieldset(
                "",
                Div(Field("email", css_class="uk-input"), css_class="uk-margin"),
                Div(Field("password", css_class="uk-input"), css_class="uk-margin"),
                css_class="uk-fieldset",
            ),
            Submit("submit", "Sign in", css_class="uk-button uk-button-primary"),
        )

        super().__init__(*args, **kwargs)

    def get_user_id(self) -> int | None:
        if self.user_cache:
            return self.user_cache.id
        return None

    def get_user(self) -> User:
        return self.user_cache

    def clean(self) -> dict:
        email = self.cleaned_data.get("email")
        password = self.cleaned_data.get("password")

        if email and password:
            try:
                user = User.objects.get(email=email)
            except ObjectDoesNotExist as e:
                user_login_failed.send(sender=User, request=self.request, credentials={"username": email})
                raise forms.ValidationError("Invalid email/password combination") from e

            self.user_cache = authenticate(request=self.request, username=user.username, password=password)

            if self.user_cache is None:
                raise forms.ValidationError("Invalid email/password combination")
            if not self.user_cache.is_active:
                raise forms.ValidationError("Your account was locked. Please contact the support.")

        return self.cleaned_data
