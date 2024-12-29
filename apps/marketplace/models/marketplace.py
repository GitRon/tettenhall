from django.db import models

from apps.item.models.item import Item
from apps.marketplace.managers.marketplace import MarketplaceManager
from apps.quest.models.quest import Quest
from apps.skirmish.models.warrior import Warrior


class Marketplace(models.Model):
    town_name = models.CharField("Town name", max_length=100)
    available_items = models.ManyToManyField(Item, verbose_name="Available items", blank=True)
    available_mercenaries = models.ManyToManyField(Warrior, verbose_name="Available mercenaries", blank=True)
    available_quests = models.ManyToManyField(Quest, verbose_name="Available quests", blank=True)

    objects = MarketplaceManager()

    class Meta:
        verbose_name = "Marketplace"
        verbose_name_plural = "Marketplaces"
        default_related_name = "marketplaces"

    def __str__(self) -> str:
        return self.town_name
