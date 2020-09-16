from django import forms
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import password_validation
from django.contrib.auth.forms import UserCreationForm

from atelier.models import User
from atelier.views.forms.auth_forms import PasswordForm
from ...view_mixins import RedirectSuccessFormMixin


class UserUpdateForm(PasswordForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'occupation', 'is_administrator', 'password1', 'password2']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
        }


class UserCreateForm(UserCreationForm, RedirectSuccessFormMixin):
    password1 = forms.CharField(
        required=True,
        label=_('Password'),
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password', 'class': 'form-control text-white', 'required': True}),
        help_text=password_validation.password_validators_help_text_html(),
    )

    password2 = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={'class': 'form-control text-white', 'required': True, 'autocomplete': 'new-password', 'id': 'materialRegisterFormPassword'}),
        strip=False,
        help_text=_('Enter the same password as before, for verification.'),
        label=_('Password confirmation'),
    )

    class Meta(RedirectSuccessFormMixin.Meta):
        model = User
        fields = RedirectSuccessFormMixin.Meta.fields + [
            'username', 'first_name', 'last_name', 'email', 'is_administrator', 'occupation', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control text-white', 'required': True}),
            'email': forms.EmailInput(attrs={'class': 'form-control text-white', 'id': 'materialRegisterFormEmail', 'required': True}),
            'first_name': forms.TextInput(
                attrs={'class': 'form-control text-white', 'id': 'materialRegisterFormFirstName', 'required': True}),
            'last_name': forms.TextInput(attrs={'class': 'form-control text-white', 'id': 'materialRegisterFormLastName', 'required': True}),
            'is_administrator': forms.CheckboxInput(attrs={'class': 'checkbox'}),
        }
