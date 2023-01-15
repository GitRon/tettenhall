# Generated by Django 4.1.5 on 2023-01-15 09:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("skirmish", "0009_skirmish_dropped_loot"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="skirmish",
            name="dropped_loot",
        ),
        migrations.AddField(
            model_name="faction",
            name="captured_warriors",
            field=models.ManyToManyField(blank=True, to="skirmish.warrior", verbose_name="Captured warriors"),
        ),
        migrations.AddField(
            model_name="faction",
            name="stored_items",
            field=models.ManyToManyField(blank=True, to="skirmish.item", verbose_name="Stored items"),
        ),
    ]
