from django.db import migrations, models


def mark_warriors_standing_in_a_pub_as_stock(apps, schema_editor):
    """
    Every man already on a pub's shelf got there by being generated for it, so the restock may go on
    clearing him out. Without this a savegame that predates the column keeps its current mercenaries
    for ever and the pub only grows.
    """
    Warrior = apps.get_model("skirmish", "Warrior")
    Warrior.objects.filter(available_pub_mercenaries__isnull=False).update(is_pub_stock=True)


class Migration(migrations.Migration):
    dependencies = [
        ("skirmish", "0010_record_what_a_fight_cost"),
    ]

    operations = [
        migrations.AddField(
            model_name="warrior",
            name="is_pub_stock",
            field=models.BooleanField(default=False, verbose_name="Is pub stock"),
        ),
        migrations.RunPython(mark_warriors_standing_in_a_pub_as_stock, migrations.RunPython.noop),
    ]
