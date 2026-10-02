import random
from unittest import mock

import pytest
from django.urls import reverse

from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.month.models.player_month_log import PlayerMonthLog
from apps.warband.quest.quests.base import QuestOutcome
from apps.warband.quest.quests.kings_summons import KingsSummons
from apps.warband.quest.tests.factories.quest_contract import QuestContractFactory
from apps.warband.skirmish.tests.factories.warrior import WarriorFactory
from apps.warband.training.models import Training
from apps.warband.training.tests.factories.training import TrainingFactory


@pytest.mark.django_db
def test_finish_month_view_brings_the_men_home_with_what_they_earned(logged_in_client, current_savegame):
    """
    Flow test, because what matters is the order the month turn runs in: the renown the quest pays
    lands in the same turn that fades an idle man's renown and trains the war band, and the man who
    was away must come out of both with his renown whole and his drill untouched.

    The draw is steered, not replaced: "random.choices" is one module object the whole month draws
    from, so only the quest's own outcomes are answered, with its success.
    """
    player_faction = current_savegame.player_faction
    TrainingFactory(faction=player_faction, category=Training.TrainingCategory.WEAPON_MASTERY)
    FactionFactory(savegame=current_savegame)
    warrior = WarriorFactory(faction=player_faction, renown=20, strength_progress=40, morale_progress=40)
    QuestContractFactory(
        faction=player_faction, quest=KingsSummons.__name__, accepted_in_month=1, assigned_warriors=[warrior]
    )
    real_choices = random.choices

    def succeed_on_the_quest(population, *args, **kwargs) -> list:
        if population and isinstance(population[0], QuestOutcome):
            return [population[0]]
        return real_choices(population, *args, **kwargs)

    with mock.patch("random.choices", side_effect=succeed_on_the_quest):
        logged_in_client.post(reverse("warband:finish-month-view"), data={"month": 1})

    warrior.refresh_from_db()
    assert (
        warrior.renown,
        warrior.strength_progress,
        warrior.morale_progress,
        PlayerMonthLog.objects.filter(faction=player_faction, month=2, title=KingsSummons.OUTCOMES[0].title).exists(),
    ) == (20 + KingsSummons.OUTCOMES[0].renown_per_man, 40, 40, True)
