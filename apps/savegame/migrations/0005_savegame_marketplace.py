# Generated by Django 4.2.17 on 2024-12-27 09:03

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("marketplace", "0003_marketplace_available_quests"),
        ("savegame", "0004_savegame_current_week"),
    ]

    operations = [
        migrations.AddField(
            model_name="savegame",
            name="marketplace",
            field=models.ForeignKey(
                default=1,
                on_delete=django.db.models.deletion.CASCADE,
                to="marketplace.marketplace",
                verbose_name="Marketplace",
            ),
            preserve_default=False,
        ),
    ]
