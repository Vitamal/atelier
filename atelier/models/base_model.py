from django.conf import settings
from django.db import models


class BaseModel(models.Model):
    created_by = models.ForeignKey(to=settings.AUTH_USER_MODEL, null=True,
                                   on_delete=models.SET_NULL, related_name='+')
    created_datetime = models.DateTimeField(auto_now_add=True)
    changed_datetime = models.DateTimeField(auto_now=True)
    changed_by = models.ForeignKey(to=settings.AUTH_USER_MODEL, null=True,
                                   on_delete=models.SET_NULL, related_name='+')

    class Meta:
        abstract = True
