# from django.contrib import messages
# from django.contrib.auth import REDIRECT_FIELD_NAME
# from django.contrib.auth.tokens import default_token_generator
# from django.shortcuts import redirect
# from django.urls import reverse
# from django.utils.translation import gettext_lazy as _
# from django.views.generic import FormView
#
# from atelier.views.forms.auth_forms import AtelierSignupForm
# from atelier.utils.env_helpers import check_if_email_is_flexit
#
#
# class SignupView(FormView):
#     """
#     Provides the ability to register as a user for employees only.
#     """
#     success_url = '/auth/login/'
#     form_class = AtelierSignupForm
#     redirect_field_name = REDIRECT_FIELD_NAME
#     template_name = 'atelier/register.html'
#
#     def get_confirmation_url(self, user):
#         token = default_token_generator.make_token(user)
#         return self.request.build_absolute_uri(reverse('confirm_email', kwargs={'user_id': user.id, 'token': token}))
#
#     def form_valid(self, form):
#         if check_if_email_is_flexit(form.instance.email):
#             messages.success(
#                 self.request,
#                 _('Your account has been created successfully. Please confirm your email to complete registration.'),
#                 extra_tags='alert-success'
#             )
#             user = form.save()
#             user.send_confirm_email_message(self.request)
#             return super(SignupView, self).form_valid(form)
#         else:
#             messages.error(
#                 self.request,
#                 _('Signup is available for Flexit employees only and requires email with "flexit.no" domain.'),
#                 extra_tags='alert-danger'
#             )
#             return redirect(reverse('index'))
