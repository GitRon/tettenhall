# Generated by Django 4.1.5 on 2023-01-22 11:27

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("item", "0007_remove_item_value_item_modifier"),
    ]

    operations = [
        migrations.AlterField(
            model_name="item",
            name="modifier",
            field=models.SmallIntegerField(default=0, help_text='2d4+7 - this is the "7"', verbose_name="Modifier"),
        ),
    ]
