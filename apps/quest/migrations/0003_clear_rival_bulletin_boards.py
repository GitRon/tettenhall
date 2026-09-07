from django.db import migrations
from django.db.models import F


def clear_rival_bulletin_boards(apps, schema_editor) -> None:
    """
    Takes the bulletin board off every faction that is not the player's.

    The board is the player's alone - nothing reads a rival's and nobody can accept off one - so the
    quests pinned to one are rows no rule touches and no monthly redraw clears.

    The quests themselves go, not just the link: a quest exists to be on a board, and one pinned to
    nothing is the same dead row in a different shape. Nothing else points at them, because
    "handle_accept_quest" takes a quest off the board when it writes the contract, so a quest still
    on one has none.
    """
    faction_model = apps.get_model("faction", "Faction")
    quest_model = apps.get_model("quest", "Quest")

    # A savegame that has not reached its player faction yet compares against NULL and drops out
    # here, which is the answer wanted: none of its factions is the player.
    player_faction_ids = faction_model.objects.filter(id=F("savegame__player_faction_id")).values("id")
    rival_factions = faction_model.objects.exclude(id__in=player_faction_ids)

    quest_model.objects.filter(available_town_quests__in=rival_factions).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("faction", "0003_faction_is_defeated"),
        ("quest", "0002_price_a_quest_against_its_target"),
    ]

    operations = [
        # Putting a rival's board back on the way down would mean inventing quests rather than
        # restoring them, so this is deliberately one-way
        migrations.RunPython(clear_rival_bulletin_boards, migrations.RunPython.noop),
    ]
