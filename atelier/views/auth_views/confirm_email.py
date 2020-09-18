from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponse
from django.utils.translation import gettext_lazy as _
from django.views.generic import RedirectView

from atelier.generic_token_with_metadata.models import GenericTokenWithMetadata, GenericTokenExpiredError


class ConfirmEmailView(RedirectView):
    url = '/auth/login/'

    def get(self, request, *args, **kwargs):
        user_id = kwargs.get('user_id')
        try:
            token = GenericTokenWithMetadata.objects.filter_usable_by_content_type_and_id_in_app(
                content_type=ContentType.objects.get_for_model(get_user_model()),
                object_id=user_id,
                app=get_user_model()._meta.app_label).get_and_check_for_single_use(token=kwargs.get('token'))
            user = token.content_object
            user.is_active = True
            user.save()
            messages.success(self.request, _('Your email was successfully confirmed!'),
                             extra_tags='alert-success alert-dismissible')
            return super().get(request, *args, **kwargs)
        except GenericTokenWithMetadata.DoesNotExist:
            return HttpResponse(_('Activation link is invalid!'))
        except GenericTokenExpiredError:
            return HttpResponse(_('The link has expired!'))
