from django.contrib.auth import logout
from django.views.generic import RedirectView


class LogoutView(RedirectView):
    """
    Provides users the ability to logout
    """
    url = '/auth/login/'

    def get(self, request, *args, **kwargs):
        logout(request)
        if 'oauth_token' in request.session:
            del request.session['oauth_token']
        return super(LogoutView, self).get(request, *args, **kwargs)
