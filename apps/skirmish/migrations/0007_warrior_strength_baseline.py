from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("skirmish", "0006_warrior_unpaid_months"),
    ]

    operations = [
        migrations.AddField(
            model_name="warrior",
            name="strength_baseline",
            # A one-off default for the warriors already on the board, not a default the model keeps.
            # Ten is the highest archetype mean in the game, so it is the conservative filling: it makes
            # nobody stronger, and every warrior generated from here on is stamped by his own generator.
            field=models.PositiveSmallIntegerField(default=10, verbose_name="Strength baseline"),
            preserve_default=False,
        ),
    ]
