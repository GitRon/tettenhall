from django.db import migrations, models

from apps.warband.warrior.services.generators.warrior.base import BaseWarriorGenerator

# How many warriors are held in memory at a time - see "0008_an_epithet_is_a_column" for why a batch
BACKFILL_BATCH_SIZE = 500


def draw_every_warriors_potential(apps, schema_editor):
    """
    Give every man made before men had a ceiling the one his generator would have drawn him.

    The rule comes from the generator rather than a copy of it, so a man migrated now and a man generated
    now are decided the same way - one distribution for every archetype, lifted to the level he stands at.
    Lifted to where he stands today rather than where he arrived, because what he arrived at is not
    recorded: a man who has climbed past the ceiling he draws has become all he will be, and drops no
    level for it. Not reproducible on purpose: a ceiling is a roll, and this is the one time it is rolled.

    Read and written in batches, the way "0008" does: every warrior of every savegame is in scope.
    """
    Warrior = apps.get_model("warband", "Warrior")
    batch = []

    for warrior in Warrior.objects.filter(potential__isnull=True).iterator(chunk_size=BACKFILL_BATCH_SIZE):
        warrior.potential = BaseWarriorGenerator.roll_potential(experience=warrior.experience)
        batch.append(warrior)

        if len(batch) == BACKFILL_BATCH_SIZE:
            Warrior.objects.bulk_update(batch, ("potential",))
            batch = []

    Warrior.objects.bulk_update(batch, ("potential",))


class Migration(migrations.Migration):
    dependencies = [
        ("warband", "0048_warrior_potential"),
    ]

    operations = [
        migrations.RunPython(draw_every_warriors_potential, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="warrior",
            name="potential",
            field=models.PositiveSmallIntegerField(verbose_name="Potential"),
        ),
    ]
