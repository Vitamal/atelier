import debug_toolbar
from django.urls import path, include

from atelier.urls import urlpatterns

urlpatterns.extend([
   path('__debug__/', include(debug_toolbar.urls)),
])
