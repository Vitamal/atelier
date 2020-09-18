from django.conf.urls import url

from flexitkt.flexitkt_email.views import email_design

urlpatterns = [
    url(r'^emaildesign/(?P<format>html|plaintext)?$', email_design.EmailDesignView.as_view()),
]
