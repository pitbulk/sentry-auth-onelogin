from __future__ import absolute_import, print_function

from sentry.auth.providers.saml2 import SAML2Provider

from .views import (
    OneloginSAML2ConfigureView, SelectIdP
)

from .constants import ONELOGIN_EMAIL, ONELOGIN_FIRSTNAME


class OneloginSAML2Provider(SAML2Provider):
    name = 'Onelogin'

    def get_configure_view(self):
        return OneloginSAML2ConfigureView.as_view()

    def get_setup_pipeline(self):
        return [
            SelectIdP()
        ]

    def build_config(self, state):
        data = super(OneloginSAML2Provider, self).build_config(state)

        if data:
            data['attribute_mapping'] = {
                'attribute_mapping_email': ONELOGIN_EMAIL,
                'attribute_mapping_firstname': ONELOGIN_FIRSTNAME
            }
        return data
