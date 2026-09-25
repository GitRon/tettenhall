import pytest

from apps.warband.quest.models.quest_type import QuestType


def test_str_is_the_name():
    quest_type = QuestType(name="Raid cattle")

    assert str(quest_type) == "Raid cattle"


@pytest.mark.django_db
def test_the_shipped_quest_types_are_half_walled():
    """
    A month's board holds one to three cards, so at one walled type in two the player is choosing
    between the two kinds nearly every month and learns to read the difference. Reference data, so
    the test reads what the fixture ships rather than building look-alikes.
    """
    walled_count = QuestType.objects.exclude(fortification_strength=0).count()

    assert (walled_count, QuestType.objects.count()) == (3, 6)
