from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("warband", "0006_a_month_log_line_says_a_rival_is_out"),
    ]

    operations = [
        migrations.AddField(
            model_name="warrior",
            name="pub_arrival_month",
            field=models.PositiveSmallIntegerField(blank=True, null=True, verbose_name="Pub arrival month"),
        ),
    ]
