from django.db import migrations, models
from django.db.models import F


def mark_every_ceiling_as_its_own_peak(apps, schema_editor):
    # Right for every warrior never cut, and it understates only the ones already cut: their loss is
    # not recorded anywhere to be recovered from, so the feast has nothing to give back to them
    apps.get_model("warband", "Warrior").objects.update(peak_max_morale=F("max_morale"))


class Migration(migrations.Migration):

    dependencies = [
        ('warband', '0017_an_incident_asks_a_question'),
    ]

    operations = [
        migrations.AddField(
            model_name='warrior',
            name='peak_max_morale',
            field=models.PositiveSmallIntegerField(default=0, verbose_name='Highest maximum morale'),
            preserve_default=False,
        ),
        migrations.RunPython(mark_every_ceiling_as_its_own_peak, migrations.RunPython.noop),
        migrations.AddField(
            model_name='town',
            name='last_feast_at',
            field=models.PositiveSmallIntegerField(default=0, help_text='Month the last feast was thrown in the hall, 0 if none was'),
        ),
        migrations.AlterField(
            model_name='playermonthlog',
            name='kind',
            field=models.PositiveSmallIntegerField(choices=[(1, 'Salaries unpaid'), (2, 'Warrior walked out'), (3, 'Salaries paid'), (4, 'Building income'), (5, 'Fyrd growth'), (6, 'Skill upgrade'), (7, 'Morale recovered'), (8, 'Wounds healed'), (9, 'Quests offered'), (10, 'Pub restocked'), (11, 'Shop restocked'), (12, 'Incident'), (13, 'Warrior dismissed'), (14, 'Morale lost over unpaid wages'), (15, 'Savegame ended'), (16, 'Rival defeated'), (17, 'Nickname earned'), (18, 'Warrior injured'), (19, 'Feast thrown')], verbose_name='Kind'),
        ),
    ]
