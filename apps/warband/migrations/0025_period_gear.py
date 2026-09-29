from django.db import migrations

# The shipped types whose name or drawing is not the fixture's any more, as (shipped name, new name, new
# icon) and back. Keyed on the name for the same reason as 0009: it is what a database already holding the
# reference table has to be matched on. The row is renamed in place, so every item of the type carries over.
RENAMED_TYPES = (
    ("Short sword", "Seax", "seax", "gladius"),
    ("Long sword", "Spatha", "spatha", "gladius"),
    ("Spear", "Spear", "spear", "spear-feather"),
    ("Battle axe", "Battle axe", "bearded-axe", "battle-axe"),
)


def arm_the_types_for_the_period(apps, schema_editor):
    ItemType = apps.get_model("warband", "ItemType")

    for shipped_name, name, svg_image_name, _ in RENAMED_TYPES:
        ItemType.objects.filter(name=shipped_name, is_fallback=False).update(
            name=name, svg_image_name=svg_image_name
        )


def restore_the_shipped_types(apps, schema_editor):
    ItemType = apps.get_model("warband", "ItemType")

    for shipped_name, name, _, shipped_svg_image_name in RENAMED_TYPES:
        ItemType.objects.filter(name=name, is_fallback=False).update(
            name=shipped_name, svg_image_name=shipped_svg_image_name
        )


class Migration(migrations.Migration):

    dependencies = [
        ("warband", "0024_a_man_has_a_face"),
    ]

    operations = [
        migrations.RunPython(arm_the_types_for_the_period, restore_the_shipped_types),
    ]
