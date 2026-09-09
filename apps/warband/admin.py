# Django's admin autodiscovery imports "<app>/admin.py" and nothing below it, so the registrations in
# the topic packages only reach the admin site through this module. A topic that registers a model admin
# has to be listed here or its pages are missing, with nothing anywhere reporting it.
import apps.warband.faction.admin
import apps.warband.finance.admin
import apps.warband.item.admin
import apps.warband.month.admin
import apps.warband.quest.admin
import apps.warband.savegame.admin
import apps.warband.skirmish.admin
import apps.warband.town.admin
import apps.warband.training.admin  # noqa: F401
