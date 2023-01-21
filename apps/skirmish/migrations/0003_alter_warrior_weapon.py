# Generated by Django 4.1.5 on 2023-01-21 14:08

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("skirmish", "0002_warrior_strength"),
    ]

    operations = [
        migrations.AlterField(
            model_name="warrior",
            name="weapon",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="warrior_weapon",
                to="skirmish.item",
                verbose_name="Weapon",
            ),
        ),
    ]
