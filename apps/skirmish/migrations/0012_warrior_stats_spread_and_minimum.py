from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("skirmish", "0011_warrior_is_pub_stock"),
    ]

    # One-off defaults for the warriors already on the board, not defaults the model keeps. Both are
    # the conservative filling, so nobody already generated is handed an epithet he did not earn: ten
    # is the widest archetype spread in the game and the widest spread puts the flattering cut-off
    # furthest away, and one is the lowest floor any archetype rolls against, which is the hardest
    # position to be sitting at.
    operations = [
        migrations.AddField(
            model_name="warrior",
            name="stats_spread",
            field=models.PositiveSmallIntegerField(default=10, verbose_name="Stats spread"),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="warrior",
            name="stats_minimum",
            field=models.PositiveSmallIntegerField(default=1, verbose_name="Stats minimum"),
            preserve_default=False,
        ),
    ]
