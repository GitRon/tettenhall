from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("skirmish", "0012_warrior_stats_spread_and_minimum"),
    ]

    # One-off defaults for the warriors already on the board, not defaults the model keeps. They are
    # the widest archetype's figures, which is the conservative filling: the highest mean and the
    # widest spread put the epithet's threshold furthest away, so nobody already generated is handed
    # one he did not earn. "nickname_variant" keeps its model default, since every wording of a state
    # says the same thing and the first is as good as any.
    operations = [
        migrations.AddField(
            model_name="warrior",
            name="health_baseline",
            field=models.PositiveSmallIntegerField(default=20, verbose_name="Health baseline"),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="warrior",
            name="health_spread",
            field=models.PositiveSmallIntegerField(default=10, verbose_name="Health spread"),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="warrior",
            name="morale_baseline",
            field=models.PositiveSmallIntegerField(default=10, verbose_name="Morale baseline"),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="warrior",
            name="morale_spread",
            field=models.PositiveSmallIntegerField(default=5, verbose_name="Morale spread"),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="warrior",
            name="nickname_variant",
            field=models.PositiveSmallIntegerField(default=0, verbose_name="Nickname variant"),
        ),
    ]
