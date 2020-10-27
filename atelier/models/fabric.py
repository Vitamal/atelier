from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from atelier.models import BaseModel


class Fabric(BaseModel):
    GROUP0 = 'GR0'
    GROUP1 = 'GR1'
    GROUP2 = 'GR2'
    GROUP3 = 'GR3'
    GROUP4 = 'GR4'
    FABRIC_GROUPS = [
        (GROUP0, _('Group 0')),
        (GROUP1, _('Group I')),
        (GROUP2, _('Group II')),
        (GROUP3, _('Group III')),
        (GROUP4, _('Group IV')),
    ]
    name = models.CharField(
        max_length=264,
        verbose_name=_('name')
    )
    group = models.CharField(
        max_length=3,
        choices=FABRIC_GROUPS,
        default=GROUP2,
        verbose_name=_('group')
    )
    complexity_factor = models.DecimalField(
        default=1,
        max_digits=5,
        decimal_places=2,
        verbose_name=_('complexity factor')
    )

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['group']

    def get_absolute_url(self):
        """
        Returns the url to access a particular client instance.
        """
        return reverse('atelier:fabric_detail', args=[str(self.id)])
