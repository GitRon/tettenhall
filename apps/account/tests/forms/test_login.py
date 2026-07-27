import pytest

from apps.account.forms.login import LoginForm
from apps.account.tests.factories.user import UserFactory


@pytest.mark.django_db
def test_get_user_id_returns_the_id_of_the_authenticated_user():
    user = UserFactory()
    login_form = LoginForm()
    login_form.user_cache = user

    assert login_form.get_user_id() == user.id


def test_get_user_id_returns_nothing_without_an_authenticated_user():
    assert LoginForm().get_user_id() is None


@pytest.mark.django_db
def test_clean_skips_the_lookup_without_credentials():
    login_form = LoginForm(data={"email": "", "password": ""})

    assert login_form.is_valid() is False
    assert login_form.non_field_errors() == []


@pytest.mark.django_db
def test_clean_rejects_an_unknown_email():
    login_form = LoginForm(data={"email": "nobody@tettenhall.test", "password": "correct-horse"})

    assert login_form.is_valid() is False
    assert login_form.non_field_errors() == ["Invalid email/password combination"]


@pytest.mark.django_db
def test_clean_rejects_an_email_shared_by_two_accounts():
    """
    "User.email" carries no uniqueness constraint, so this used to raise MultipleObjectsReturned and
    answer the login page with a 500.
    """
    UserFactory(username="beorn", email="shared@tettenhall.test")
    UserFactory(username="cuthred", email="shared@tettenhall.test")
    login_form = LoginForm(data={"email": "shared@tettenhall.test", "password": "correct-horse"})

    assert login_form.is_valid() is False
    assert login_form.non_field_errors() == ["Invalid email/password combination"]


@pytest.mark.django_db
def test_clean_rejects_an_inactive_account(rf):
    user = UserFactory(email="beorn@tettenhall.test", is_active=False)
    user.set_password("correct-horse")
    user.save()

    login_form = LoginForm(
        request=rf.post("/login/"), data={"email": "beorn@tettenhall.test", "password": "correct-horse"}
    )

    assert login_form.is_valid() is False
    assert login_form.non_field_errors() == ["Invalid email/password combination"]
