from django.db import migrations


def create_missing_towns(apps, schema_editor) -> None:  # noqa: PBR001 (RunPython calls this positionally)
    """
    Gives every faction that predates the town app a town of its own.

    A faction owns exactly one town and several handlers dereference "faction.town" unconditionally,
    so a faction without one makes finishing a month, selling an item, restocking the shop and
    healing a warrior raise Town.DoesNotExist and roll the whole queuebie chain back.
    """
    faction_model = apps.get_model("faction", "Faction")
    town_model = apps.get_model("town", "Town")

    town_model.objects.bulk_create(
        town_model(faction=faction) for faction in faction_model.objects.filter(town__isnull=True)
    )


class Migration(migrations.Migration):
    dependencies = [
        ("faction", "0001_initial"),
        ("town", "0004_alter_town_last_constructed_building_at"),
    ]

    operations = [
        # Deleting the towns again on the way back would take the buildings of factions that always
        # had one with them, so this is deliberately one-way
        migrations.RunPython(create_missing_towns, migrations.RunPython.noop),
    ]
