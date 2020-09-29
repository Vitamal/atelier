from django.contrib import messages
from django.contrib.auth import authenticate, login, REDIRECT_FIELD_NAME
from django.shortcuts import redirect, reverse
from django.template.loader import get_template
from django.utils.translation import ugettext
from django.views.generic import TemplateView

from atelier.models import User
from atelier.atelier_email.emailutils import convert_html_to_plaintext
from atelier.atelier_messages.models import SystemMessage
from atelier.generic_token_with_metadata.models import GenericTokenWithMetadata
from atelier.views.forms.auth_forms import GetMobileCodeForm, EmailLoginForm

PHONE_TYPE = 'mobile'
EMAIL_TYPE = 'email'


class LoginView(TemplateView):
    template_name = 'atelier/authentication/login.html'
    redirect_field_name = REDIRECT_FIELD_NAME

    @staticmethod
    def normalize_phone_number(phone_number):
        return phone_number.strip().replace(' ', '').replace('-', '')

    @staticmethod
    def get_auth_code(user, code_type):
        return GenericTokenWithMetadata.objects.generate_short_living_token(
            app=User._meta.app_label, content_object=user, minutes=5, metadata={'type': code_type, 'attempts': 3},
            length=4
        ).token

    @property
    def next(self):
        return self.request.POST.get('next')

    def get_success_redirect(self):
        return redirect(self.next if self.next else reverse('index'))

    @staticmethod
    def get_self_redirect():
        return redirect(reverse('login'))

    @staticmethod
    def get_confirm_redirect(user, code_type):
        return redirect(reverse('confirm_code', kwargs={'user_id': user.id, 'type': code_type}))

    def send_login_code(self, request, user, warning, code_type, email=None):
        if not user:
            messages.warning(request, warning, extra_tags='alert-warning')
            return self.get_self_redirect()
        code = self.get_auth_code(user, code_type)
        html_message = get_template('atelier/emails/login_code_message.html').render(
            context={'name': user.get_full_name(), 'code': code})
        message_dict = dict(
            subject=ugettext('Atelier authentication code'),
            message_content_html=html_message,
            message_content_plain=convert_html_to_plaintext(html_message),
            email_heading=ugettext('Atelier authentication')
        )
        message_dict.update(
            dict(to_phone_number=user.phone_number) if code_type == PHONE_TYPE else dict(
                to_email=email if email is not None else user.email))
        SystemMessage.objects.send(**message_dict)
        return self.get_confirm_redirect(user, code_type)

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return self.get_success_redirect()
        return super().get(request, *args, **kwargs)

    @staticmethod
    def get_active_user_by_email(email):
        try:
            user = User.objects.filter(email=email, is_active=True).get()
        except User.DoesNotExist:
            return None
        return user

    def post(self, request, *args, **kwargs):
        if 'phone_number' in request.POST:
            phone = self.normalize_phone_number(request.POST.get('phone_number'))
            user = User.objects.filter(phone_number__endswith=phone, is_active=True).first()
            warning = ugettext('We could not find a user registered with this phone number. '
                               'Try to log in using email address, or register to create an account.')
            return self.send_login_code(request, user, warning, PHONE_TYPE)

        provided_email = request.POST.get('email')
        user_from_email = self.get_active_user_by_email(provided_email)
        if 'email_code' in request.POST:
            warning = ugettext('We could not find a user registered with this email. '
                               'Try to log in using phone number, or register to create an account.')
            return self.send_login_code(request, user_from_email, warning, EMAIL_TYPE, provided_email)

        user = authenticate(email=provided_email, password=request.POST.get('password'))
        # user = authenticate(email=user_from_email.email, password=request.POST.get('password')
        #                     ) if user_from_email is not None else None
        if user is not None:
            login(request, user)
            return self.get_success_redirect()

        messages.error(request,
                       ugettext('The provided email or password is invalid. Make sure you provide correct credentials'),
                       extra_tags='alert-danger')
        return self.get_self_redirect()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['get_mobile_code_form'] = GetMobileCodeForm()
        context['email_login_form'] = EmailLoginForm()
        return context
