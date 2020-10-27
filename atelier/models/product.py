from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from atelier.models import BaseModel
from atelier.models.atelier import Atelier


class Product(BaseModel):
    name = models.CharField(
        max_length=264,
        verbose_name=_('name')
    )
    basic_product = models.ForeignKey(
        'atelier.BasicProduct',
        on_delete=models.CASCADE,
        verbose_name=_('basic product')
    )
    base_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_('base price')
    )
    atelier = models.ForeignKey(
        Atelier,
        on_delete=models.CASCADE,
        verbose_name=_('Atelier'),
    )

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']

    def get_absolute_url(self):
        return reverse('atelier:product_detail', args=[str(self.id)])
