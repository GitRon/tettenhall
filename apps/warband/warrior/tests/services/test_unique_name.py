from unittest import mock

import pytest

from apps.faker_old_english import BYNAMES, OLD_ENGLISH_LOCALE
from apps.warband.faction.models.culture import Culture
from apps.warband.skirmish.models.warrior import Warrior
from apps.warband.skirmish.tests.factories.warrior import WarriorFactory
from apps.warband.warrior.services.unique_name import NAME_DRAW_ATTEMPTS, _disambiguate, draw_warrior_name

# Faker is third party and random by nature, so the draws are handed in rather than waited for -
# a collision that only sometimes happens is a branch that only sometimes runs.
FAKER_PATH = "apps.warband.faction.services.faker.Faker"


def test_disambiguate_takes_a_byname():
    result = _disambiguate(name="Wulfstan", names_in_play={"Wulfstan"}, locale=OLD_ENGLISH_LOCALE)

    assert result == f"Wulfstan {BYNAMES[0]}"


def test_disambiguate_numbers_the_man_once_the_bynames_are_gone():
    """
    Reachable only by a war band holding every byname on one given name, and it still may not raise
    and may not spin.
    """
    names_in_play = {"Wulfstan"} | {f"Wulfstan {byname}" for byname in BYNAMES}

    result = _disambiguate(name="Wulfstan", names_in_play=names_in_play, locale=OLD_ENGLISH_LOCALE)

    assert result == "Wulfstan 2"


def test_disambiguate_counts_past_a_number_already_taken():
    names_in_play = {"Wulfstan", "Wulfstan 2"} | {f"Wulfstan {byname}" for byname in BYNAMES}

    result = _disambiguate(name="Wulfstan", names_in_play=names_in_play, locale=OLD_ENGLISH_LOCALE)

    assert result == "Wulfstan 3"


def test_disambiguate_numbers_a_culture_with_no_bynames():
    result = _disambiguate(name="Bjorn", names_in_play={"Bjorn"}, locale="no_NO")

    assert result == "Bjorn 2"


@pytest.mark.django_db
def test_draw_warrior_name_keeps_the_first_draw():
    culture = Culture.objects.get(locale=OLD_ENGLISH_LOCALE)
    warrior = WarriorFactory(name="Eadric")

    with mock.patch(FAKER_PATH, return_value=mock.Mock(first_name_male=mock.Mock(side_effect=["Wulfstan"]))):
        result = draw_warrior_name(culture=culture, savegame_id=warrior.savegame_id)

    assert result == "Wulfstan"


@pytest.mark.django_db
def test_draw_warrior_name_draws_again_after_a_collision():
    culture = Culture.objects.get(locale=OLD_ENGLISH_LOCALE)
    warrior = WarriorFactory(name="Wulfstan")

    with mock.patch(FAKER_PATH, return_value=mock.Mock(first_name_male=mock.Mock(side_effect=["Wulfstan", "Eadric"]))):
        result = draw_warrior_name(culture=culture, savegame_id=warrior.savegame_id)

    assert result == "Eadric"


@pytest.mark.django_db
def test_draw_warrior_name_disambiguates_once_the_draws_run_out():
    culture = Culture.objects.get(locale=OLD_ENGLISH_LOCALE)
    warrior = WarriorFactory(name="Wulfstan")

    with mock.patch(
        FAKER_PATH, return_value=mock.Mock(first_name_male=mock.Mock(side_effect=["Wulfstan"] * NAME_DRAW_ATTEMPTS))
    ):
        result = draw_warrior_name(culture=culture, savegame_id=warrior.savegame_id)

    assert result == f"Wulfstan {BYNAMES[0]}"


@pytest.mark.django_db
def test_draw_warrior_name_leaves_a_dead_mans_name_free():
    """
    Uniqueness is against the living. Held against every row ever written, a long game would drive
    every draw into the fallback.
    """
    culture = Culture.objects.get(locale=OLD_ENGLISH_LOCALE)
    warrior = WarriorFactory(name="Wulfstan", condition=Warrior.ConditionChoices.CONDITION_DEAD)

    with mock.patch(FAKER_PATH, return_value=mock.Mock(first_name_male=mock.Mock(side_effect=["Wulfstan"]))):
        result = draw_warrior_name(culture=culture, savegame_id=warrior.savegame_id)

    assert result == "Wulfstan"


@pytest.mark.django_db
def test_draw_warrior_name_ignores_another_savegame():
    culture = Culture.objects.get(locale=OLD_ENGLISH_LOCALE)
    WarriorFactory(name="Wulfstan")
    warrior_of_this_savegame = WarriorFactory(name="Eadric")

    with mock.patch(FAKER_PATH, return_value=mock.Mock(first_name_male=mock.Mock(side_effect=["Wulfstan"]))):
        result = draw_warrior_name(culture=culture, savegame_id=warrior_of_this_savegame.savegame_id)

    assert result == "Wulfstan"
