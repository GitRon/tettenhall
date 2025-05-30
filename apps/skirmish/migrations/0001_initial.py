# Generated by Django 5.1.7 on 2025-03-16 10:37

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("faction", "0001_initial"),
        ("item", "0001_initial"),
        ("savegame", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Skirmish",
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
                ("name", models.CharField(max_length=100, verbose_name="Name")),
                (
                    "current_round",
                    models.PositiveSmallIntegerField(
                        default=1, verbose_name="Current round"
                    ),
                ),
                (
                    "non_player_faction",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="non_player_skirmishes",
                        to="faction.faction",
                        verbose_name="Non-player faction",
                    ),
                ),
                (
                    "player_faction",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="player_skirmishes",
                        to="faction.faction",
                        verbose_name="Player faction",
                    ),
                ),
                (
                    "victorious_faction",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="victorious_skirmishes",
                        to="faction.faction",
                        verbose_name="Victorious faction",
                    ),
                ),
            ],
            options={
                "verbose_name": "Skirmish",
                "verbose_name_plural": "Skirmishes",
                "default_related_name": "skirmishes",
            },
        ),
        migrations.CreateModel(
            name="BattleHistory",
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
                ("message", models.TextField(verbose_name="Message")),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="Created at"),
                ),
                (
                    "skirmish",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="skirmish.skirmish",
                        verbose_name="Skirmish",
                    ),
                ),
            ],
            options={
                "verbose_name": "Battle log",
                "verbose_name_plural": "Battle logs",
                "default_related_name": "battle_logs",
            },
        ),
        migrations.CreateModel(
            name="Warrior",
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
                ("name", models.CharField(max_length=100, verbose_name="Name")),
                (
                    "avatar_id",
                    models.PositiveSmallIntegerField(
                        default=1, verbose_name="Avatar-ID"
                    ),
                ),
                ("strength", models.PositiveSmallIntegerField(verbose_name="Strength")),
                (
                    "strength_progress",
                    models.PositiveSmallIntegerField(
                        default=0, verbose_name="Strength progress"
                    ),
                ),
                (
                    "dexterity",
                    models.PositiveSmallIntegerField(verbose_name="Dexterity"),
                ),
                (
                    "dexterity_progress",
                    models.PositiveSmallIntegerField(
                        default=0, verbose_name="Dexterity progress"
                    ),
                ),
                (
                    "current_health",
                    models.SmallIntegerField(verbose_name="Current health"),
                ),
                (
                    "max_health",
                    models.PositiveSmallIntegerField(verbose_name="Maximum health"),
                ),
                (
                    "health_progress",
                    models.PositiveSmallIntegerField(
                        default=0, verbose_name="Health progress"
                    ),
                ),
                (
                    "current_morale",
                    models.SmallIntegerField(verbose_name="Current morale"),
                ),
                (
                    "max_morale",
                    models.PositiveSmallIntegerField(verbose_name="Maximum morale"),
                ),
                (
                    "morale_progress",
                    models.PositiveSmallIntegerField(
                        default=0, verbose_name="Morale progress"
                    ),
                ),
                (
                    "experience",
                    models.PositiveIntegerField(default=0, verbose_name="Experience"),
                ),
                (
                    "monthly_salary",
                    models.PositiveSmallIntegerField(
                        default=0, verbose_name="Monthly salary"
                    ),
                ),
                (
                    "recruitment_price",
                    models.PositiveSmallIntegerField(
                        default=0, verbose_name="Recruitment price"
                    ),
                ),
                (
                    "condition",
                    models.PositiveSmallIntegerField(
                        choices=[
                            (1, "Healthy"),
                            (2, "Unconscious"),
                            (3, "Fleeing"),
                            (4, "Dead"),
                        ],
                        default=1,
                        verbose_name="Condition",
                    ),
                ),
                (
                    "armor",
                    models.OneToOneField(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="warrior_armor",
                        to="item.item",
                        verbose_name="Armor",
                    ),
                ),
                (
                    "culture",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="faction.culture",
                        verbose_name="Culture",
                    ),
                ),
                (
                    "faction",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="faction.faction",
                        verbose_name="Faction",
                    ),
                ),
                (
                    "savegame",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="savegame.savegame",
                        verbose_name="Savegame",
                    ),
                ),
                (
                    "weapon",
                    models.OneToOneField(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="warrior_weapon",
                        to="item.item",
                        verbose_name="Weapon",
                    ),
                ),
            ],
            options={
                "verbose_name": "Warrior",
                "verbose_name_plural": "Warriors",
                "default_related_name": "warriors",
            },
        ),
        migrations.AddField(
            model_name="skirmish",
            name="non_player_warriors",
            field=models.ManyToManyField(
                related_name="non_player_skirmishes",
                to="skirmish.warrior",
                verbose_name="Non-player warriors",
            ),
        ),
        migrations.AddField(
            model_name="skirmish",
            name="player_warriors",
            field=models.ManyToManyField(
                related_name="player_skirmishes",
                to="skirmish.warrior",
                verbose_name="Player warriors",
            ),
        ),
    ]
