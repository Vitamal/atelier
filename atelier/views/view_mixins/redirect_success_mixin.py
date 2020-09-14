from abc import ABCMeta

from django import forms


class RedirectSuccessFormMixin(forms.Form):
    # To be used with RedirectSuccessMixin

    success_url = forms.CharField(required=False, widget=forms.HiddenInput(attrs={'hide_label': True}))

    class Meta:
        fields = ['success_url']


class RedirectSuccessMixin(metaclass=ABCMeta):
    # To be used after Create or Update View, together with RedirectSuccessFormMixin

    _re = False
    re_attribute = ('re', 'true')
    _re_id_name = 'id'

    def get_success_url(self):
        return '{}?{}={}'.format(self._re, self._re_id_name, getattr(self, 'object').id) if self._re else getattr(
            super(), 'get_success_url')()

    def get_initial(self):
        initial = getattr(super(), 'get_initial')()
        if getattr(self, 'request').method.lower() == 'get' and getattr(
                self, 'request').GET.get(self.re_attribute[0], False) == self.re_attribute[1]:
            self._re = getattr(self, 'request').META.get('HTTP_REFERER', False)
            if self._re:
                initial.update({'success_url': self._re})
        return initial

    def form_valid(self, form):
        self._re = form.data.get('success_url', False)
        return getattr(super(), 'form_valid')(form)

    def get_basic_cancel_url(self):
        raise NotImplementedError()

    def get_cancel_url(self):
        return self._re or self.get_basic_cancel_url()

    def get_context_data(self, **kwargs):
        context = getattr(super(), 'get_context_data')(**kwargs)
        context['cancel_url'] = self.get_cancel_url()
        return context
