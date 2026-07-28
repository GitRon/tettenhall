from django.db import models
from django.db.models import manager


class ItemQuerySet(models.QuerySet):
    def for_savegame(self, *, savegame_id: int):
        return self.filter(savegame_id=savegame_id)

    def for_player_faction(self, *, faction_id: int):
        return self.filter(owner_id=faction_id)

    def on_sale_at(self, *, faction_id: int):
        # Shop membership is the town's "available_items", not a missing owner: the equipment of
        # the pub mercenaries is unowned too, and that is not for sale
        return self.filter(available_shop_items=faction_id)


class ItemManager(manager.Manager):
    def update_ownership(self, *, item, new_owner):
        from apps.skirmish.models.warrior import Warrior

        # Reset ownership
        item.owner = new_owner
        item.save()

        # Remove from current usages
        Warrior.objects.filter(weapon=item).update(weapon=None)
        Warrior.objects.filter(armor=item).update(armor=None)

        return item


ItemManager = ItemManager.from_queryset(ItemQuerySet)
