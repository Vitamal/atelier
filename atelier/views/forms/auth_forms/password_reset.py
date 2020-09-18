from django.utils.translation import gettext as _
from django import forms

from atelier.models import User


class PasswordResetForm(forms.Form):

    error_messages = {'no_email': _('There is no user with given email')}
    user = None

    email = forms.EmailField(
        required=True, label=_('Your Email'),
        widget=forms.EmailInput(attrs={'class': 'form-control', 'required': True}),
    )

    def clean_email(self):
        email = self.cleaned_data.get('email')
        try:
            self.user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise forms.ValidationError(self.error_messages['no_email'], code='no_email')
        return email
