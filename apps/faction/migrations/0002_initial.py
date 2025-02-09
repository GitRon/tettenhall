# Generated by Django 5.1.6 on 2025-02-09 10:52

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("faction", "0001_initial"),
        ("quest", "0001_initial"),
        ("savegame", "0001_initial"),
        ("skirmish", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="faction",
            name="active_quests",
            field=models.ManyToManyField(
                blank=True,
                help_text="There can only be one active quest at a time.",
                to="quest.questcontract",
                verbose_name="Active Quest",
            ),
        ),
        migrations.AddField(
            model_name="faction",
            name="captured_warriors",
            field=models.ManyToManyField(
                blank=True, to="skirmish.warrior", verbose_name="Captured warriors"
            ),
        ),
        migrations.AddField(
            model_name="faction",
            name="culture",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to="faction.culture",
                verbose_name="Culture",
            ),
        ),
        migrations.AddField(
            model_name="faction",
            name="savegame",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to="savegame.savegame",
                verbose_name="Savegame",
            ),
        ),
    ]
