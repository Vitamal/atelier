from django.utils.translation import gettext as _
from ievv_opensource.utils import choices_with_meta

DEFAULT_CURRENCY = 'UAH'


class MetaChoice(choices_with_meta.Choice):
    def __init__(self, value, label=None, description='', attributename=None, **kwargs):
        super().__init__(value, label, description, attributename)
        for k, v in kwargs.items():
            setattr(self, k, v)


AVAILABLE_CURRENCIES = choices_with_meta.ChoicesWithMeta(
    MetaChoice(value='UAH', label='UAH', description=_('Ukrainian hryvnia'), sign='hrn'),
    MetaChoice(value='EUR', label='EUR', description=_('Euro'), sign='eur'),
)


def get_sign_by_value(value):
    return AVAILABLE_CURRENCIES.get_by_value(value).sign
