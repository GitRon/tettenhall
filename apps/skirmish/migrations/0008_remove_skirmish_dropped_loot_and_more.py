# Generated by Django 4.1.5 on 2023-01-15 09:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("skirmish", "0007_remove_skirmish_non_player_warriors_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="skirmish",
            name="dropped_loot",
        ),
        migrations.AddField(
            model_name="skirmish",
            name="non_player_warriors",
            field=models.ManyToManyField(
                related_name="non_player_skirmishes", to="skirmish.warrior", verbose_name="Non-player warriors"
            ),
        ),
    ]
