# Generated by Django 5.1.6 on 2025-02-09 10:52

import apps.common.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("faction", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="ItemType",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=75, verbose_name="Name")),
                (
                    "function",
                    models.PositiveSmallIntegerField(
                        choices=[(1, "Weapon"), (2, "Armor")], verbose_name="Function"
                    ),
                ),
                (
                    "base_value",
                    models.CharField(
                        max_length=10,
                        validators=[apps.common.validators.dice_notation],
                        verbose_name="Value",
                    ),
                ),
                (
                    "svg_image_name",
                    models.CharField(max_length=50, verbose_name="SVG image name"),
                ),
                (
                    "is_fallback",
                    models.BooleanField(default=0, verbose_name="Is fallback"),
                ),
            ],
            options={
                "verbose_name": "Item type",
                "verbose_name_plural": "Item types",
                "default_related_name": "item_types",
            },
        ),
        migrations.CreateModel(
            name="Item",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "condition",
                    models.PositiveSmallIntegerField(
                        choices=[
                            (1, "Rusty"),
                            (2, "Cheap"),
                            (3, "Traditional"),
                            (4, "Superior"),
                        ],
                        default=3,
                        verbose_name="Condition",
                    ),
                ),
                ("price", models.PositiveSmallIntegerField(verbose_name="Price")),
                (
                    "modifier",
                    models.SmallIntegerField(
                        default=0,
                        help_text='2d4+7 - this is the "7"',
                        verbose_name="Modifier",
                    ),
                ),
                (
                    "owner",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="faction.faction",
                        verbose_name="Owning faction",
                    ),
                ),
            ],
            options={
                "verbose_name": "Item",
                "verbose_name_plural": "Items",
                "default_related_name": "items",
            },
        ),
    ]
