import pytest
from django.urls import reverse

from apps.skirmish.tests.factories.battle_history import BattleHistoryFactory
from apps.skirmish.tests.factories.skirmish import SkirmishFactory


@pytest.mark.django_db
def test_battle_history_update_htmx_view_lists_the_history_of_the_skirmish(logged_in_client, current_savegame):
    skirmish = SkirmishFactory(player_faction=current_savegame.player_faction)
    battle_history = BattleHistoryFactory(skirmish=skirmish)

    response = logged_in_client.get(reverse("skirmish:battle-history-update-htmx", kwargs={"skirmish_id": skirmish.id}))

    assert response.status_code == 200
    assert list(response.context["battlehistory_list"]) == [battle_history]


@pytest.mark.django_db
def test_battle_history_update_htmx_view_hides_history_of_another_savegame(logged_in_client, current_savegame):
    other_skirmish = SkirmishFactory()
    BattleHistoryFactory(skirmish=other_skirmish)

    response = logged_in_client.get(
        reverse("skirmish:battle-history-update-htmx", kwargs={"skirmish_id": other_skirmish.id})
    )

    assert response.status_code == 200
    assert list(response.context["battlehistory_list"]) == []
