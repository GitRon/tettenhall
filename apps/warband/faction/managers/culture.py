from ambient_toolbox.managers import GetOrNoneManagerMixin
from django.db import models
from django.db.models import manager


class CultureQuerySet(models.QuerySet):
    pass


class CultureManager(GetOrNoneManagerMixin, manager.Manager):
    pass


CultureManager = CultureManager.from_queryset(CultureQuerySet)
