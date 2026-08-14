import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("faction", "0001_initial"),
        ("skirmish", "0004_skirmish_month"),
    ]

    operations = [
        migrations.RenameField(
            model_name="skirmish",
            old_name="player_faction",
            new_name="attacking_faction",
        ),
        migrations.RenameField(
            model_name="skirmish",
            old_name="non_player_faction",
            new_name="defending_faction",
        ),
        migrations.RenameField(
            model_name="skirmish",
            old_name="player_warriors",
            new_name="attacking_warriors",
        ),
        migrations.RenameField(
            model_name="skirmish",
            old_name="non_player_warriors",
            new_name="defending_warriors",
        ),
        migrations.AlterField(
            model_name="skirmish",
            name="attacking_faction",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="attacking_skirmishes",
                to="faction.faction",
                verbose_name="Attacking faction",
            ),
        ),
        migrations.AlterField(
            model_name="skirmish",
            name="defending_faction",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="defending_skirmishes",
                to="faction.faction",
                verbose_name="Defending faction",
            ),
        ),
        migrations.AlterField(
            model_name="skirmish",
            name="attacking_warriors",
            field=models.ManyToManyField(
                related_name="attacking_skirmishes",
                to="skirmish.warrior",
                verbose_name="Attacking warriors",
            ),
        ),
        migrations.AlterField(
            model_name="skirmish",
            name="defending_warriors",
            field=models.ManyToManyField(
                related_name="defending_skirmishes",
                to="skirmish.warrior",
                verbose_name="Defending warriors",
            ),
        ),
    ]
