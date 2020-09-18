from django import forms
from django.contrib.auth import password_validation, get_user_model
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from atelier.views.forms.widgets import FriendlyPasswordInputWidget


def email_validator(value):
    if get_user_model().objects.filter(email=value).exists():
        raise ValidationError(
            _(f'User with email address {value} alredy exists. Please use another email'
              f' or use "Forgot password" link on log in page to restore access.'))


class AtelierSignupForm(forms.ModelForm):
    email = forms.EmailField(
        label=_('Email address'),
        required=True,
        validators=[email_validator],
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )

    password1 = forms.CharField(
        label=_("Password"),
        strip=False,
        widget=FriendlyPasswordInputWidget(attrs={'autocomplete': 'new-password', 'class': 'form-control'}),
        help_text=password_validation.password_validators_help_text_html(),
    )

    class Meta:
        model = get_user_model()
        fields = ("email", "first_name", "last_name")
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'})
        }

    def save(self, commit=True):
        self.instance.username = self.instance.email
        self.instance.is_active = False
        self.instance.set_password(self.cleaned_data["password1"])
        return super().save(commit)

    def _post_clean(self):
        super()._post_clean()
        # Validate the password after self.instance is updated with form data
        # by super().
        password = self.cleaned_data.get('password1')
        if password:
            try:
                password_validation.validate_password(password, self.instance)
            except forms.ValidationError as error:
                self.add_error('password1', error)
