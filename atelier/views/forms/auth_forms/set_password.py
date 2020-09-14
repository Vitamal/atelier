from django import forms
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import password_validation

from atelier.models import User


class PasswordForm(forms.ModelForm):

    error_messages = {'password_mismatch': _('The two password fields didn’t match.')}

    def __init__(self, *args, **kwargs):
        self.user = kwargs.get('instance')
        super().__init__(*args, **kwargs)

    password1 = forms.CharField(
        required=False,
        label=_('Password'),
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password', 'class': 'form-control', 'required': False}),
        help_text=password_validation.password_validators_help_text_html(),
    )

    password2 = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'new-password', 'required': False}),
        strip=False,
        help_text=_('Enter the same password as before, for verification.'),
        label=_('Password confirmation'),
    )

    class Meta:
        model = User
        fields = ['password1', 'password2']

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2:
            if password1 != password2:
                raise forms.ValidationError(
                    self.error_messages['password_mismatch'],
                    code='password_mismatch',
                )
        if password1:
            password_validation.validate_password(password2, self.user)
        return password2

    def save(self, commit=True):
        """Save the new password."""
        password = self.cleaned_data["password1"]
        if password:
            self.user.set_password(password)
        if commit:
            self.user.save()
        return self.user
