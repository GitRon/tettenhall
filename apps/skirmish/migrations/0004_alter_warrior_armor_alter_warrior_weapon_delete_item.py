# Generated by Django 4.1.5 on 2023-01-21 14:55

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("item", "0001_initial"),
        ("skirmish", "0003_alter_warrior_weapon"),
    ]

    operations = [
        migrations.AlterField(
            model_name="warrior",
            name="armor",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="warrior_armor",
                to="item.item",
                verbose_name="Armor",
            ),
        ),
        migrations.AlterField(
            model_name="warrior",
            name="weapon",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="warrior_weapon",
                to="item.item",
                verbose_name="Weapon",
            ),
        ),
        migrations.DeleteModel(
            name="Item",
        ),
    ]
