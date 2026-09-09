from django.db import models


class QuestName(models.Model):
    """
    The pool of errands a bulletin board draws its cards from.

    Reference data shipped as a fixture, like cultures and item types, so the wording of what the
    game offers is content rather than a literal in a generator. A quest keeps the name it was pinned
    to the board under - "Quest.name" is its own column - so rewriting the pool changes what the next
    board offers and leaves every contract already signed reading as it did.
    """

    name = models.CharField("Name", max_length=50)

    class Meta:
        verbose_name = "Quest name"
        verbose_name_plural = "Quest names"
        default_related_name = "quest_names"

    def __str__(self) -> str:
        return self.name
