# Generated by Django 4.1.5 on 2023-01-20 17:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("skirmish", "0013_alter_warrior_condition"),
    ]

    operations = [
        migrations.AddField(
            model_name="warrior",
            name="experience",
            field=models.PositiveIntegerField(default=0, verbose_name="Experience"),
        ),
    ]
