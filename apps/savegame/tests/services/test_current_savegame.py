import pytest
from django.test import RequestFactory

from apps.savegame.services.current_savegame import get_current_savegame_for_request


@pytest.mark.django_db
def test_resolves_the_active_savegame_of_the_requesting_user(user, current_savegame):
    request = RequestFactory().get("/")
    request.user = user

    assert get_current_savegame_for_request(request=request) == current_savegame


@pytest.mark.django_db
def test_asks_the_database_once_per_request(user, current_savegame, django_assert_num_queries):
    """
    The whole point of the resolver: four context processors and every scoping mixin ask this on a
    single render, and the answer cannot change between them.
    """
    request = RequestFactory().get("/")
    request.user = user

    with django_assert_num_queries(1):
        first = get_current_savegame_for_request(request=request)
        second = get_current_savegame_for_request(request=request)

    assert first == second == current_savegame


@pytest.mark.django_db
def test_answers_none_without_an_active_savegame(user):
    request = RequestFactory().get("/")
    request.user = user

    assert get_current_savegame_for_request(request=request) is None


@pytest.mark.django_db
def test_caches_the_absence_of_a_savegame_too(user, django_assert_num_queries):
    """
    None is an answer like any other, and a "if not hasattr" that tested the value instead of the
    attribute would re-query on every caller for exactly the users who have no savegame.
    """
    request = RequestFactory().get("/")
    request.user = user

    with django_assert_num_queries(1):
        first = get_current_savegame_for_request(request=request)
        second = get_current_savegame_for_request(request=request)

    assert first is second is None
