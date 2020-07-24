from ievv_opensource.utils import ievvbuildstatic

import atelier
# from atelier_javascript.js_buildstatic_app import JsBuildStaticApp
from .develop_and_test_settings_common import *
import socket

# from ...atelier_bootstrap.flexit_cssbuild_plugin import FlexitBuildCssPlugin

LANGUAGE_CODE = 'en'

INSTALLED_APPS += [
    'ievv_opensource.ievv_developemail',
    'debug_toolbar',
    'ievv_opensource.ievvtasks_common',

]

EMAIL_BACKEND = 'ievv_opensource.ievv_developemail.email_backend.DevelopEmailBackend'

MIDDLEWARE += [
    'debug_toolbar.middleware.DebugToolbarMiddleware'
]

# hostname, _, ips = socket.gethostbyname_ex(socket.gethostname())
# INTERNAL_IPS = [ip[:-1] + '1' for ip in ips] + ['127.0.0.1', '10.0.2.2']
#
#
# IEVVTASKS_BUILDSTATIC_APPS = ievvbuildstatic.config.Apps(
#     ievvbuildstatic.config.App(
#         appname='atelier_bootstrap',
#         version=atelier.MAJOR_VERSION,
#         plugins=[
#
#             # Build the main css
#             FlexitBuildCssPlugin(
#                 sourcefolder='scss',
#                 sourcefile='main.scss',
#             ),
#         ]
#     ),
#     FlexitktJsBuildStaticApp(
#         appname='atelier_javascript',
#         version=atelier.MAJOR_VERSION,
#         plugins=[
#             ievvbuildstatic.npmrun_jsbuild.Plugin(),
#             ievvbuildstatic.npmrun.Plugin(script='i18n-build', group='i18n')
#         ]
#     )
# )
