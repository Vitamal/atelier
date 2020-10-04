from django.contrib import messages
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.tokens import default_token_generator
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView

from atelier.models import Atelier
from atelier.views.forms.auth_forms import AtelierSignupForm


class SignupView(FormView):
    """
    Provides the ability to register as a user for employees only.
    """
    success_url = '/auth/login/'
    form_class = AtelierSignupForm
    redirect_field_name = REDIRECT_FIELD_NAME
    template_name = 'atelier/authentication/register.html'

    def get_confirmation_url(self, user):
        token = default_token_generator.make_token(user)
        return self.request.build_absolute_uri(reverse('confirm_email', kwargs={'user_id': user.id, 'token': token}))

    def form_valid(self, form):
        messages.success(
            self.request,
            _('Your account has been created successfully. Please confirm your email to complete registration.'),
            extra_tags='alert-success'
        )
        atelier = Atelier.objects.create(name='Test')
        form.instance.atelier = atelier
        user = form.save()
        user.send_confirm_email_message(self.request)
        return super(SignupView, self).form_valid(form)
