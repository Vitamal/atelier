from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils.translation import gettext

from atelier.views.forms.auth_forms import PasswordForm


class MyProfileForm(PasswordForm):
    class Meta:
        model = get_user_model()
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'password1', 'password2']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control text-white'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control text-white'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control text-white', 'required': True}),
            'last_name': forms.TextInput(attrs={'class': 'form-control text-white', 'required': True}),
        }

    def clean_email(self):
        if get_user_model().objects.filter(username=self.data.get('email')).exclude(id=self.instance.id).exists():
            raise ValidationError(gettext('User with such email already exists.'))
        return self.data.get('email')
