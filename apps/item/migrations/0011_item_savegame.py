# Generated by Django 5.1.4 on 2025-01-01 08:49

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("item", "0010_alter_item_condition"),
        ("savegame", "0009_alter_savegame_current_week"),
    ]

    operations = [
        migrations.AddField(
            model_name="item",
            name="savegame",
            field=models.ForeignKey(
                default=2,
                on_delete=django.db.models.deletion.CASCADE,
                to="savegame.savegame",
                verbose_name="Savegame",
            ),
            preserve_default=False,
        ),
    ]
