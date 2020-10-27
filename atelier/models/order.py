from django.db import models
import datetime
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from atelier.utils import order_price_calculation
from django.contrib.auth import get_user_model
from atelier.models import BaseModel, Atelier


class Order(BaseModel):

    # function to set Django model date field 'deadline' of default value to future date
    def return_date_time():
        return datetime.date.today() + datetime.timedelta(weeks=2)

    CATEGORY1 = '1'
    CATEGORY2 = '2'
    PROCESSING_CATEGORY = [
        (CATEGORY1, 'Processing category 1'),
        (CATEGORY2, 'Processing category 2'),
    ]
    customer = models.ForeignKey(
        'atelier.Customer',
        on_delete=models.CASCADE,
        verbose_name=_('customer')
    )
    product = models.ForeignKey(
        'atelier.Product',
        on_delete=models.CASCADE,
        verbose_name=_('product')
    )
    fabric = models.ForeignKey(
        'atelier.Fabric',
        on_delete=models.CASCADE,
        verbose_name=_('fabric')
    )
    processing_category = models.CharField(
        max_length=1,
        choices=PROCESSING_CATEGORY,
        default=CATEGORY2,
        verbose_name=_('processing category')
    )
    complication_elements = models.ManyToManyField(
        'atelier.ComplicationElement',
        blank=True,
        verbose_name=_('complication elements')
    )
    allowance_discount = models.ManyToManyField(
        'atelier.AllowanceDiscount',
        blank=True,
        verbose_name=_('allowance/discount')
    )
    order_date = models.DateField(
        default=datetime.date.today,
        verbose_name=_('order date')
    )
    performer = models.ForeignKey(
        get_user_model(),  # will return the currently active user model
        on_delete=models.CASCADE,
        verbose_name=_('performer'),
        null=True,
    )
    deadline = models.DateField(
        default=return_date_time(),
        # migration doesn't call it, so it will be evaluated by django when creating an instance
        null=True,
        blank=True,
        verbose_name=_('deadline')
    )
    atelier = models.ForeignKey(
        Atelier,
        on_delete=models.CASCADE,
        verbose_name=_('atelier'),
    )
    is_closed = models.BooleanField(
        default=False,
        blank=True,
        verbose_name=_('closed')
    )

    class Meta:
        ordering = ["order_date"]

    def __str__(self):
        """
        to display an object in the Django admin site
        and as the value inserted into a template when it displays an object
        """
        return '{} {}'.format(self.customer, self.order_date)

    def display_allowance_discount(self):
        """
        Creates a string for the allowance_discount. This is required to display allowance_discount in Admin.
        """
        return ', '.join([allowance_discount.name for allowance_discount in self.allowance_discount.all()[:3]])

    display_allowance_discount.short_description = _('allowance/discount')

    def display_complication_elements(self):
        """
        Creates a string for the complication_elements. This is required to display complication_elements in Admin.
        """
        return ', '.join([complication_elements.name for complication_elements in self.complication_elements.all()[:3]])

    display_complication_elements.short_description = _('complication elements')

    def get_absolute_url(self):
        """
        Returns the url to access a particular instance.
        """
        return reverse('atelier:order_detail', args=[str(self.id)])

    @property
    def order_price(self):

        complication_elements_base_price_list = []
        complication_elements_complexity_list = []
        allowance_discount_coefficient_list = []

        for i in self.complication_elements.all():
            complication_elements_base_price_list.append(i.base_price)
            complication_elements_complexity_list.append(i.complexity)

        for k in self.allowance_discount.all():
            allowance_discount_coefficient_list.append(k.coefficient)

        return order_price_calculation(self.fabric.complexity_factor, self.product.base_price,
                                       complication_elements_base_price_list, complication_elements_complexity_list,
                                       self.processing_category, allowance_discount_coefficient_list)
