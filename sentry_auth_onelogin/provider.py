from __future__ import absolute_import, print_function

from django.conf import settings
from sentry.auth import AuthView, Provider
from sentry.http import safe_urlopen, safe_urlread
from sentry.utils import json
from urllib import urlencode

from .mixins import SamlMixin
from .views import SamlAcs, SamlConfigure, SamlRequest

from onelogin.saml2.auth import OneLogin_Saml2_Auth
from onelogin.saml2.settings import OneLogin_Saml2_Settings
from onelogin.saml2.utils import OneLogin_Saml2_Utils


class OneLoginProvider(Provider, SamlMixin):
    def __init__(self, connector_id=None, connector_cert=None, **config):
        self.connector_id = connector_id
        self.connector_cert = connector_cert
        super(Provider, self).__init__(**config)

    def get_auth_pipeline(self):
        config = self.build_auth(
            connector_id=self.connector_id,
            connector_cert=self.connector_cert,
            entity_id=absolute_uri(),
            # TODO: is this actually required? if so we need to know how
            # to generate a url from the following pipeline, which is
            # a bit painful
            acs_url="",
        )
        return [
            SamlRequest(config=config),
            SamlAcs(config=config),
        ]

    def get_setup_pipeline(self):
        """
        Return a list of AuthView instances representing the initial setup
        pipeline for this provider.

        Defaults to the defined authentication pipeline.
        """
        return [
            SamlConfigure(),
        ]


    def get_identity(self, state):
        user_data = state['data']
        return {
            # TODO: is there a "correct" email?
            'email': None,
            'name': None,
        }
