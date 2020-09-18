from django import forms
from django.utils.translation import ugettext


class ConfirmCodeForm(forms.Form):
    code = forms.CharField(
        label=ugettext('Enter code here'),
        widget=forms.TextInput(attrs={'class': 'form-control', 'autofocus': 'autofocus'})
    )
