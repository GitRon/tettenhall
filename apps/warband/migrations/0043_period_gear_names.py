from django.db import migrations

# The shipped types whose name is not the fixture's any more, as (shipped name, new name). Keyed on the name
# for the same reason as 0009: it is what a database already holding the reference table has to be matched
# on. The row is renamed in place, so every item of the type carries over; the icons already fit the period.
RENAMED_TYPES = (
    ("Studded leather", "Leather jerkin"),
    ("Battle axe", "Bearded axe"),
)


def name_the_types_for_the_period(apps, schema_editor):
    ItemType = apps.get_model("warband", "ItemType")

    for shipped_name, name in RENAMED_TYPES:
        ItemType.objects.filter(name=shipped_name, is_fallback=False).update(name=name)


def restore_the_shipped_names(apps, schema_editor):
    ItemType = apps.get_model("warband", "ItemType")

    for shipped_name, name in RENAMED_TYPES:
        ItemType.objects.filter(name=name, is_fallback=False).update(name=shipped_name)


class Migration(migrations.Migration):

    dependencies = [
        ("warband", "0042_the_fallen_are_named"),
    ]

    operations = [
        migrations.RunPython(name_the_types_for_the_period, restore_the_shipped_names),
    ]
