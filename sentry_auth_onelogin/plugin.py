from __future__ import absolute_import, print_function

from sentry.plugins import Plugin2

from .provider import OneLoginProvider


class OneLoginAuthPlugin(Plugin2):
    def get_auth_providers(self):
        return [OneLoginProvider]
