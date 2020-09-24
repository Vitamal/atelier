from django import forms
from django.utils.translation import ugettext


class EmailLoginForm(forms.Form):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(
            attrs={'class': 'form-control', 'placeholder': ugettext('Your email address'),
                   'required': True, 'hide_label': True})
    )

    password = forms.CharField(
        required=False,
        strip=False,
        widget=forms.PasswordInput(
            attrs={'autocomplete': 'new-password', 'class': 'form-control', 'required': False,
                   'placeholder': ugettext('Your password'), 'hide_label': True}),
    )
