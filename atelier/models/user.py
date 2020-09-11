from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext as _
from ievv_opensource.utils import choices_with_meta

from atelier.models import Atelier

INTERN = 'intern'
SEAMSTRESS = 'seamstress'
DESIGNER = 'designer'
TAILOR = 'tailor'
OCCUPATIONS = [INTERN, SEAMSTRESS, DESIGNER, TAILOR]
OCCUPATIONS_CHOICES = choices_with_meta.ChoicesWithMeta(
    choices_with_meta.Choice(value=INTERN, label=_('Intern'), description=_(
        'Click to hide questions that require high technical level')),
    choices_with_meta.Choice(value=SEAMSTRESS, label=_('Seamstress'), description=_(
        'Click to hide questions that require high technical level')),
    choices_with_meta.Choice(value=DESIGNER, label=_('Designer'), description=_(
        'Click to also show questions that require high technical level')),
    choices_with_meta.Choice(value=TAILOR, label=_('Tailor'), description=_(
        'Click to also show questions that require very high technical level')),
)


def true_if_superuser(m):
    def wrapper_true_if_superuser(instance, *args, **kwargs):
        return True if instance.is_superuser else m(instance, *args, **kwargs)

    return wrapper_true_if_superuser


class User(AbstractUser):
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    # __app_access_dict = None
    INTERN = INTERN
    SEAMSTRESS = SEAMSTRESS
    DESIGNER = DESIGNER
    TAILOR = TAILOR
    OCCUPATIONS_CHOICES = OCCUPATIONS_CHOICES

    email = models.EmailField(_('email address'), blank=True, unique=True, null=True, default=None)
    phone_number = models.CharField(max_length=20, null=False, blank=True, default='')
    occupation = models.CharField(
        max_length=10, choices=OCCUPATIONS_CHOICES.iter_as_django_choices_short(), default=SEAMSTRESS,
        verbose_name=_('Occupation')
    )
    atelier = models.ForeignKey(Atelier, on_delete=models.CASCADE, verbose_name=_('atelier'))
    is_administrator = models.BooleanField(null=False, blank=False, default=False)

    def save(self, *args, **kwargs):
        if self.email == '':
            self.email = None
        return super().save(*args, **kwargs)

    # for empty string email, if user has not email
    def validate_unique(self, exclude=None):
        if self.email in ['', None]:
            exclude.append('email')
        return super().validate_unique(exclude)

    def __str__(self):
        return self.get_full_name()

    def get_full_name(self):
        name = super().get_full_name()
        if not name:
            return self.email
        return name

    # ????
    @true_if_superuser
    def is_admin(self):
        return self.is_administrator
