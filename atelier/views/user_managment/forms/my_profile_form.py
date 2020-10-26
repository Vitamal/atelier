from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.images import get_image_dimensions
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

    def clean_avatar(self):
        avatar = self.cleaned_data['avatar']

        try:
            w, h = get_image_dimensions(avatar)

            # validate dimensions
            max_width = max_height = 100
            if w > max_width or h > max_height:
                raise forms.ValidationError(
                    u'Please use an image that is '
                    '%s x %s pixels or smaller.' % (max_width, max_height))

            # validate content type
            main, sub = avatar.content_type.split('/')
            if not (main == 'image' and sub in ['jpeg', 'pjpeg', 'gif', 'png']):
                raise forms.ValidationError(u'Please use a JPEG, '
                                            'GIF or PNG image.')

            # validate file size
            if len(avatar) > (20 * 1024):
                raise forms.ValidationError(
                    u'Avatar file size may not exceed 20k.')

        except AttributeError:
            """
            Handles case when we are updating the user profile
            and do not supply a new avatar
            """
            pass

        return avatar
