from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("skirmish", "0011_warrior_is_pub_stock"),
    ]

    operations = [
        migrations.AddField(
            model_name="warrior",
            name="stats_spread",
            # A one-off default for the warriors already on the board, not a default the model keeps.
            # Ten is the widest archetype spread in the game, so it is the conservative filling: the
            # wider the spread, the further from the mean a roll has to sit to count as extreme, and
            # nobody already generated is handed an epithet he did not earn.
            field=models.PositiveSmallIntegerField(default=10, verbose_name="Stats spread"),
            preserve_default=False,
        ),
    ]
