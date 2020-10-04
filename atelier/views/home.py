from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView


# class HomePageView(LoginRequiredMixin, TemplateView):
class HomePageView(TemplateView):
    template_name = 'atelier/home.html'
