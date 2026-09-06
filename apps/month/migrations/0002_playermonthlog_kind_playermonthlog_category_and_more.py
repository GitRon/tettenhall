from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("month", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="playermonthlog",
            name="kind",
            field=models.PositiveSmallIntegerField(
                choices=[
                    (1, "Salaries unpaid"),
                    (2, "Warrior deserted"),
                    (3, "Salaries paid"),
                    (4, "Building income"),
                    (5, "Fyrd growth"),
                    (6, "Skill upgrade"),
                    (7, "Morale recovered"),
                    (8, "Wounds healed"),
                ],
                # Rows already in the table were written before a kind existed and are swept at the
                # next month advance, so they are given the one value that says nothing about them
                # rather than a guess. The model itself carries no default: a producer that forgets
                # to name its kind should fail loudly.
                default=3,
                verbose_name="Kind",
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="playermonthlog",
            name="category",
            field=models.PositiveSmallIntegerField(
                choices=[(1, "Demands attention"), (2, "Consequence"), (3, "Upkeep")],
                default=2,
                verbose_name="Category",
            ),
            preserve_default=False,
        ),
        migrations.AlterModelOptions(
            name="playermonthlog",
            options={
                "default_related_name": "player_month_logs",
                "ordering": ("-month", "id"),
                "verbose_name": "Player month log",
                "verbose_name_plural": "Player month logs",
            },
        ),
    ]
