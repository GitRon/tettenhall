# Generated by Django 4.1.5 on 2023-01-20 20:49

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("finance", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="transaction",
            name="amount",
            field=models.IntegerField(verbose_name="Amount"),
        ),
    ]
