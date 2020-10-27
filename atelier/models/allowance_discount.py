from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from atelier.models import BaseModel


class AllowanceDiscount(BaseModel):
    name = models.CharField(
        max_length=255,
        verbose_name=_('name')
    )
    coefficient = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name=_('coefficient')
    )
    label = models.CharField(
        max_length=255,
        verbose_name=_('group')
    )

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']

    def get_absolute_url(self):
        """
        Returns the url to access a particular instance.
        """
        return reverse('atelier:allowance_discount_detail', args=[str(self.id)])
