from __future__ import absolute_import, print_function

from sentry.auth.providers.saml2 import SAML2Provider

from .views import (
    OneLoginSAML2ConfigureView, OneLoginSelectIdP
)

from .constants import ONELOGIN_EMAIL, ONELOGIN_USERNAME, ONELOGIN_DISPLAYNAME


class OneLoginSAML2Provider(SAML2Provider):
    name = 'Onelogin'

    def get_configure_view(self):
        return OneLoginSAML2ConfigureView.as_view()

    def get_setup_pipeline(self):
        return [
            OneLoginSelectIdP()
        ]

    def build_config(self, state):
        data = super(OneLoginSAML2Provider, self).build_config(state)

        if data:
            data['attribute_mapping'] = {
                'attribute_mapping_email': ONELOGIN_EMAIL,
                'attribute_mapping_username': ONELOGIN_USERNAME,
                'attribute_mapping_displayname': ONELOGIN_DISPLAYNAME
            }
        return data
