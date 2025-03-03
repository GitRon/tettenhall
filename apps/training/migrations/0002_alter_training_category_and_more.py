# Generated by Django 5.1.6 on 2025-03-03 13:45

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("faction", "0003_faction_leader"),
        ("training", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="training",
            name="category",
            field=models.PositiveSmallIntegerField(
                choices=[(1, "Weapon mastery"), (2, "Swiftness"), (3, "Shield wall")],
                verbose_name="Category",
            ),
        ),
        migrations.AddConstraint(
            model_name="training",
            constraint=models.UniqueConstraint(
                fields=("faction", "category"), name="unique_faction_category"
            ),
        ),
    ]
