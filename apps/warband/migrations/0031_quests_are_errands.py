import django.db.models.deletion
from django.db import migrations, models



def delete_quest_rows_without_a_new_meaning(apps, schema_editor):
    """
    The quest-reward spoils and the "quests offered" log lines describe a kind of quest that no longer
    exists, so they go with it. The month cannot end with a fight open, so no contract is mid-skirmish
    when this runs: dropping the quest tables below loses the current month's board and nothing else.
    """
    apps.get_model("warband", "SkirmishSpoil").objects.filter(kind=3).delete()
    apps.get_model("warband", "PlayerMonthLog").objects.filter(kind=9).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('warband', '0030_the_fyrd_raises_a_leader'),
    ]

    operations = [
        migrations.RunPython(delete_quest_rows_without_a_new_meaning, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='faction',
            name='active_quests',
        ),
        migrations.RemoveField(
            model_name='faction',
            name='available_quests',
        ),
        migrations.DeleteModel(
            name='QuestContract',
        ),
        migrations.DeleteModel(
            name='Quest',
        ),
        migrations.DeleteModel(
            name='QuestType',
        ),
        migrations.RemoveField(
            model_name='skirmishspoil',
            name='description',
        ),
        migrations.AlterField(
            model_name='skirmishspoil',
            name='kind',
            field=models.PositiveSmallIntegerField(choices=[(1, 'Item taken'), (2, 'Silver looted')], verbose_name='Kind'),
        ),
        migrations.AlterField(
            model_name='playermonthlog',
            name='kind',
            field=models.PositiveSmallIntegerField(choices=[(1, 'Salaries unpaid'), (2, 'Warrior walked out'), (3, 'Salaries paid'), (4, 'Building income'), (5, 'Fyrd growth'), (6, 'Skill upgrade'), (7, 'Morale recovered'), (8, 'Wounds healed'), (10, 'Pub restocked'), (11, 'Shop restocked'), (12, 'Incident'), (13, 'Warrior dismissed'), (14, 'Morale lost over unpaid wages'), (15, 'Savegame ended'), (16, 'Rival defeated'), (17, 'Nickname earned'), (18, 'Warrior injured'), (19, 'Feast thrown'), (20, 'Warrior changed'), (21, 'Harvest'), (22, 'Leader succeeded'), (23, 'Leader raised from the fyrd'), (24, 'Quest returned')], verbose_name='Kind'),
        ),
        migrations.CreateModel(
            name='Quest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('month', models.PositiveSmallIntegerField(verbose_name='Offered in month')),
                ('quest', models.CharField(max_length=50, verbose_name='Quest')),
                ('title', models.CharField(max_length=100, verbose_name='Title')),
                ('body', models.TextField(blank=True, default='', verbose_name='Body')),
                ('faction', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='warband.faction', verbose_name='Offered to')),
            ],
            options={
                'verbose_name': 'Quest',
                'verbose_name_plural': 'Quests',
                'ordering': ('id',),
                'default_related_name': 'quests',
            },
        ),
        migrations.CreateModel(
            name='QuestContract',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quest', models.CharField(max_length=50, verbose_name='Quest')),
                ('title', models.CharField(max_length=100, verbose_name='Title')),
                ('accepted_in_month', models.PositiveSmallIntegerField(verbose_name='Accepted in month')),
                ('resolved_in_month', models.PositiveSmallIntegerField(blank=True, null=True, verbose_name='Resolved in month')),
                ('assigned_warriors', models.ManyToManyField(to='warband.warrior', verbose_name='Assigned warriors')),
                ('faction', models.ForeignKey(help_text='Faction who sent men on the quest.', on_delete=django.db.models.deletion.CASCADE, to='warband.faction')),
            ],
            options={
                'verbose_name': 'Quest contract',
                'verbose_name_plural': 'Quest contracts',
                'ordering': ('id',),
                'default_related_name': 'quest_contracts',
            },
        ),
    ]
