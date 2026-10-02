from django.db import migrations

# NPC_STARTING_FORTIFICATION_LEVEL, the Palisade, written out: a migration has to keep meaning what it
# meant when it ran, whatever the level list becomes
PALISADE_LEVEL = 1


def raise_the_wall_of_every_rival_town(apps, schema_editor):
    """
    A rival is created behind a Palisade. A savegame started before towns had walls gave every town the
    column's default of none, so its rivals are raised to the wall a new rival gets.

    A rival's wall never moves in play, so a rival town on no wall is one from before walls existed.
    The player's own town starts at none and is left there.
    """
    Town = apps.get_model("warband", "Town")

    Town.objects.filter(fortification=0, faction__player_savegame__isnull=True).update(fortification=PALISADE_LEVEL)


class Migration(migrations.Migration):

    dependencies = [
        ('warband', '0036_a_title_holds_any_name'),
    ]

    operations = [
        migrations.RunPython(raise_the_wall_of_every_rival_town, migrations.RunPython.noop),
    ]
