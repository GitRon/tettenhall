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
        from apps.warband.skirmish.models.warrior import Warrior

        # Reset ownership
        item.owner = new_owner
        item.save()

        # Remove from current usages
        Warrior.objects.filter(weapon=item).update(weapon=None)
        Warrior.objects.filter(armor=item).update(armor=None)

        return item

    def hand_over(self, *, item, previous_owner, new_owner) -> bool:
        """
        Move the item to "new_owner" only if "previous_owner" still holds it, and say whether it moved.

        One conditional UPDATE rather than update_ownership's read-modify-save, because buying and
        selling are paid for: two overlapping requests both find the item where the page showed it,
        and only the one that actually moves it may be charged or paid. "previous_owner" None is the
        shop's own stock, which is generated unowned.
        """
        from apps.warband.skirmish.models.warrior import Warrior

        moved_rows = self.filter(pk=item.pk, owner=previous_owner).update(owner=new_owner)
        if not moved_rows:
            return False

        # The UPDATE went around the instance, so bring it in line for the handlers downstream
        item.owner = new_owner

        # Remove from current usages
        Warrior.objects.filter(weapon=item).update(weapon=None)
        Warrior.objects.filter(armor=item).update(armor=None)

        return True


ItemManager = ItemManager.from_queryset(ItemQuerySet)
