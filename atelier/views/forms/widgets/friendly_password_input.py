from django.forms import widgets


class FriendlyPasswordInputWidget(widgets.PasswordInput):
    """
    Widget to draw password input, with possibility to make password visible
    To be used with friendly_password.js
    """
    template_name = 'atelier/widgets/friendly_password_input.html'
