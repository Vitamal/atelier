from django import forms
from django.utils.translation import ugettext


class GetMobileCodeForm(forms.Form):
    phone_number = forms.CharField(
        min_length=10,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control', 'placeholder': ugettext('Your mobile number'), 'required': True,
            'hide_label': True})
    )
