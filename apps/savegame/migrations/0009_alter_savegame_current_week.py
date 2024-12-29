# Generated by Django 5.1.4 on 2024-12-29 08:12

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("savegame", "0008_alter_savegame_marketplace_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="savegame",
            name="current_week",
            field=models.PositiveSmallIntegerField(
                default=0,
                help_text="Week will be incremented after creation via Command",
                verbose_name="Current week",
            ),
        ),
    ]
