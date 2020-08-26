from atelier.models import BaseModel
from django.db import models

from atelier.utils.currency_helper import DEFAULT_CURRENCY, AVAILABLE_CURRENCIES


class Atelier(BaseModel):
    name = models.CharField(max_length=255, db_index=True)
    place = models.CharField(max_length=255, null=False, blank=True, default='')
    currency_code = models.CharField(
        max_length=3, null=False, default=DEFAULT_CURRENCY,
        choices=AVAILABLE_CURRENCIES.iter_as_django_choices_short()
    )
    post_code = models.CharField(max_length=5, null=False, blank=True, default='')

    addressline = models.CharField(max_length=255, null=False, blank=True, default='')

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']

    @property
    def full_address(self):
        return f'{self.addressline}, {self.post_code} {self.place}'
