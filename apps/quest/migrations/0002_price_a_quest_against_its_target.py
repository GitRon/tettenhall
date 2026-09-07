from django.db import migrations, models

# The top of each difficulty's band, from "Quest.get_min_max_number_of_opponents". Copied rather than
# imported: a migration has to keep describing the schema it was written against, and the model is
# free to move its bands afterwards.
BAND_MAXIMUM_BY_DIFFICULTY = {1: 5, 2: 8}


def price_existing_quests_against_a_full_band(apps, schema_editor) -> None:
    """
    Gives every quest pinned to a board before this field the war band its purse was rolled for.

    "Quest.loot" is scaled by "expected_opposition" over the band maximum, so the band maximum is the
    value that leaves an already-advertised purse worth exactly what it says. Anything smaller would
    reprice a contract the player may have accepted already.
    """
    quest_model = apps.get_model("quest", "Quest")

    for difficulty, band_maximum in BAND_MAXIMUM_BY_DIFFICULTY.items():
        quest_model.objects.filter(difficulty=difficulty).update(expected_opposition=band_maximum)


class Migration(migrations.Migration):
    dependencies = [
        ("quest", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="quest",
            name="expected_opposition",
            field=models.PositiveSmallIntegerField(default=0, verbose_name="Expected opposition"),
            # The zero is scaffolding for the rows that already exist, filled in below. The field
            # itself has no default: a quest is priced by the generator that writes it, and one that
            # skipped that step would quietly advertise nothing.
            preserve_default=False,
        ),
        # Dropping the column again on the way back loses nothing, so this needs no reverse
        migrations.RunPython(price_existing_quests_against_a_full_band, migrations.RunPython.noop),
    ]
