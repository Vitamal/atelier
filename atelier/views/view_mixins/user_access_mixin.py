from abc import ABCMeta
from gettext import gettext

from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.utils.translation import gettext


class UserManagementAccessMixin(UserPassesTestMixin, metaclass=ABCMeta):
    permission_denied_message = gettext(
        "You have no permission to view this page. Please contact site administrator to get access."
    )

    def test_func(self):
        """
        access for ateliers administrators only
        """
        return getattr(self, 'request').user.is_authenticated and (
                getattr(self, 'request').user.is_superuser or getattr(self, 'request').user.is_administrator)

    def dispatch(self, request, *args, **kwargs):
        if not getattr(self, 'request').user.is_authenticated:
            messages.warning(
                request,
                gettext('The page you are trying to see has restricted access. Please login to continue.'),
                extra_tags='alert-warning'
            )
        return super().dispatch(request, *args, **kwargs)
