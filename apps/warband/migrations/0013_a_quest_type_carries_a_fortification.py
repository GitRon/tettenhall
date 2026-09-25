from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('warband', '0012_a_fight_says_how_it_sorts'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='QuestName',
            new_name='QuestType',
        ),
        migrations.AlterModelOptions(
            name='questtype',
            options={'default_related_name': 'quest_types', 'verbose_name': 'Quest type', 'verbose_name_plural': 'Quest types'},
        ),
        migrations.AddField(
            model_name='questtype',
            name='fortification_strength',
            field=models.PositiveSmallIntegerField(default=0, verbose_name='Fortification strength'),
        ),
        migrations.AddField(
            model_name='quest',
            name='fortification_strength',
            field=models.PositiveSmallIntegerField(default=0, verbose_name='Fortification strength'),
        ),
    ]
