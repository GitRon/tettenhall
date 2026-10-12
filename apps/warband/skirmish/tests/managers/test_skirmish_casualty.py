import pytest

from apps.warband.skirmish.models.skirmish_casualty import SkirmishCasualty
from apps.warband.skirmish.tests.factories.skirmish import SkirmishFactory
from apps.warband.skirmish.tests.factories.skirmish_casualty import SkirmishCasualtyFactory
from apps.warband.skirmish.tests.factories.warrior import WarriorFactory


@pytest.mark.django_db
def test_create_record_creates_the_row_on_the_first_fate():
    skirmish = SkirmishFactory()
    warrior = WarriorFactory(faction=skirmish.attacking_faction)

    casualty = SkirmishCasualty.objects.create_record(
        skirmish=skirmish, warrior=warrior, fate=SkirmishCasualty.FateChoices.FATE_KILLED
    )

    assert casualty.fate == SkirmishCasualty.FateChoices.FATE_KILLED
    assert SkirmishCasualty.objects.count() == 1


@pytest.mark.django_db
def test_create_record_overwrites_the_fate_of_a_man_already_recorded():
    """
    The case of every prisoner in the game: knocked out first, taken once the fight was decided.
    """
    existing = SkirmishCasualtyFactory(fate=SkirmishCasualty.FateChoices.FATE_INCAPACITATED)

    casualty = SkirmishCasualty.objects.create_record(
        skirmish=existing.skirmish, warrior=existing.warrior, fate=SkirmishCasualty.FateChoices.FATE_CAPTURED
    )

    assert casualty.fate == SkirmishCasualty.FateChoices.FATE_CAPTURED
    assert SkirmishCasualty.objects.count() == 1


@pytest.mark.django_db
def test_create_record_stamps_the_killer_and_the_leader_flag():
    skirmish = SkirmishFactory()
    warrior = WarriorFactory(faction=skirmish.attacking_faction)
    killer = WarriorFactory(faction=skirmish.defending_faction)

    casualty = SkirmishCasualty.objects.create_record(
        skirmish=skirmish,
        warrior=warrior,
        fate=SkirmishCasualty.FateChoices.FATE_KILLED,
        killed_by=killer,
        fell_as_a_leader=True,
    )

    assert (casualty.killed_by, casualty.fell_as_a_leader) == (killer, True)


@pytest.mark.django_db
def test_for_skirmish_keeps_another_fights_casualty_out():
    casualty = SkirmishCasualtyFactory()
    SkirmishCasualtyFactory()

    result = SkirmishCasualty.objects.for_skirmish(skirmish_id=casualty.skirmish_id)

    assert list(result) == [casualty]


@pytest.mark.django_db
def test_killed_of_faction_keeps_the_dead_of_one_faction():
    killed = SkirmishCasualtyFactory()
    faction = killed.warrior.faction
    # Not killed, and killed for somebody else: neither is this faction's dead
    SkirmishCasualtyFactory(
        skirmish=killed.skirmish,
        warrior__faction=faction,
        fate=SkirmishCasualty.FateChoices.FATE_INCAPACITATED,
    )
    SkirmishCasualtyFactory(skirmish=killed.skirmish, warrior__faction=killed.skirmish.defending_faction)

    result = SkirmishCasualty.objects.killed_of_faction(faction_id=faction.id)

    assert list(result) == [killed]
