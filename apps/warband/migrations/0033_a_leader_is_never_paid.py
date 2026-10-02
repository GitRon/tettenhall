from django.db import migrations


def take_every_leader_off_the_payroll(apps, schema_editor):
    """
    The leader draws no wage. A man who took the seat in a savegame started before that rule kept the
    wage he was hired at, so every man holding a seat now is put off the payroll and owed nothing.
    """
    Faction = apps.get_model("warband", "Faction")
    Warrior = apps.get_model("warband", "Warrior")

    Warrior.objects.filter(
        id__in=Faction.objects.filter(leader__isnull=False).values("leader_id")
    ).update(monthly_salary=0, unpaid_months=0)


class Migration(migrations.Migration):

    dependencies = [
        ('warband', '0032_quests_are_errands'),
    ]

    operations = [
        migrations.RunPython(take_every_leader_off_the_payroll, migrations.RunPython.noop),
    ]
