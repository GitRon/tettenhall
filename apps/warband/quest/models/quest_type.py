from django.db import models


class QuestType(models.Model):
    """
    The kinds of errand a bulletin board draws its cards from.

    Reference data shipped as a fixture, like cultures and item types, so what the game offers - the
    wording and the numbers behind it - is content rather than a literal in a generator. A quest
    copies what it needs off its type when it is pinned to the board ("Quest.name",
    "Quest.fortification_strength") instead of pointing at it: an accepted quest is a contract, so
    rewriting the pool changes what the next board offers and leaves every contract already signed
    reading and paying as it did.
    """

    name = models.CharField("Name", max_length=50)
    # 0 for an errand in open country. A settlement errand stands behind a wall of this strength,
    # on the same scale the attack path puts in front of a rival's town.
    fortification_strength = models.PositiveSmallIntegerField("Fortification strength", default=0)

    class Meta:
        verbose_name = "Quest type"
        verbose_name_plural = "Quest types"
        default_related_name = "quest_types"

    def __str__(self) -> str:
        return self.name
