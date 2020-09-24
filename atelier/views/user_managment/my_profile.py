from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django.utils.translation import gettext
from django.views.generic.edit import UpdateView

from atelier.models import User
from atelier.views.user_managment.forms.my_profile_form import MyProfileForm


class MyProfileView(LoginRequiredMixin, UpdateView):
    model = User
    template_name = 'atelier/user_management/my_profile.html'
    context_object_name = 'user'
    form_class = MyProfileForm

    def get_success_url(self):
        return reverse('index')

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        if 'email' in form.changed_data:
            form.instance.username = form.cleaned_data.get('email')
            form.instance.is_active = False
            user = form.save()
            user.send_confirm_email_message(self.request)
            logout(self.request)
            messages.warning(
                self.request,
                gettext('Please check your inbox and confirm your email address before trying to login!'),
                extra_tags='alert-warning'
            )
        return super().form_valid(form)
