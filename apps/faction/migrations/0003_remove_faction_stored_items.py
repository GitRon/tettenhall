# Generated by Django 4.1.5 on 2023-01-21 13:57

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("faction", "0002_initial"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="faction",
            name="stored_items",
        ),
    ]
