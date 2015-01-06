from __future__ import absolute_import, print_function

from django.conf import settings
from sentry.auth import AuthView, Provider
from sentry.http import safe_urlopen, safe_urlread
from sentry.utils import json
from urllib import urlencode

from onelogin.saml2.auth import OneLogin_Saml2_Auth
from onelogin.saml2.settings import OneLogin_Saml2_Settings
from onelogin.saml2.utils import OneLogin_Saml2_Utils


ERR_ACS_FAILURE = 'There was an error authenticating you with the provider.'


class SamlMixin(object):
    def build_config(self, connector_id, connector_cert, entity_id, acs_url):
        return {
            # If strict is True, then the Python Toolkit will reject unsigned
            # or unencrypted messages if it expects them to be signed or encrypted.
            # Also it will reject the messages if the SAML standard is not strictly
            # followed. Destination, NameId, Conditions ... are validated too.
            "strict": True,

            # Enable debug mode (outputs errors).
            "debug": settings.DEBUG,

            # Service Provider Data that we are deploying.
            "sp": {
                # Identifier of the SP entity  (must be a URI)
                "entityId": entity_id,

                # Specifies info about where and how the <AuthnResponse> message MUST be
                # returned to the requester, in this case our SP.
                "assertionConsumerService": {
                    # URL Location where the <Response> from the IdP will be returned
                    "url": acs_url,
                    # SAML protocol binding to be used when returning the <Response>
                    # message. OneLogin Toolkit supports this endpoint for the
                    # HTTP-POST binding only.
                    "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST"
                },

                # Specifies info about where and how the <Logout Response> message MUST be
                # returned to the requester, in this case our SP.
                "singleLogoutService": {
                    # URL Location where the <Response> from the IdP will be returned
                    "url": "https://<sp_domain>/?sls",
                    # SAML protocol binding to be used when returning the <Response>
                    # message. OneLogin Toolkit supports the HTTP-Redirect binding
                    # only for this endpoint.
                    "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"
                },
                # Specifies the constraints on the name identifier to be used to
                # represent the requested subject.
                # Take a look on src/onelogin/saml2/constants.py to see the NameIdFormat that are supported.
                "NameIDFormat": "urn:oasis:names:tc:SAML:2.0:nameid-format:unspecified",
                # Usually x509cert and privateKey of the SP are provided by files placed at
                # the certs folder. But we can also provide them with the following parameters
                'x509cert' => '',
                'privateKey' => ''
            },

            # Identity Provider Data that we want connected with our SP.
            "idp": {
                # Identifier of the IdP entity  (must be a URI)
                "entityId": "https://app.onelogin.com/saml/metadata/%s" % (connector_id,),
                # SSO endpoint info of the IdP. (Authentication Request protocol)
                "singleSignOnService": {
                    # URL Target of the IdP where the Authentication Request Message
                    # will be sent.
                    "url": "https://app.onelogin.com/trust/saml2/http-post/sso/%s" % (connector_id,),
                    # SAML protocol binding to be used when returning the <Response>
                    # message. OneLogin Toolkit supports the HTTP-Redirect binding
                    # only for this endpoint.
                    "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"
                },
                # SLO endpoint info of the IdP.
                "singleLogoutService": {
                    # URL Location of the IdP where SLO Request will be sent.
                    "url": "https://app.onelogin.com/trust/saml2/http-redirect/slo/%s" % (connector_id,),
                    # SAML protocol binding to be used when returning the <Response>
                    # message. OneLogin Toolkit supports the HTTP-Redirect binding
                    # only for this endpoint.
                    "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"
                },
                # Public x509 certificate of the IdP
                "x509cert": connector_cert,
                /*
                 *  Instead of use the whole x509cert you can use a fingerprint
                 *  (openssl x509 -noout -fingerprint -in "idp.crt" to generate it)
                 */
                # "certFingerprint": ""
            },
            "contactPerson": {
                "technical": {
                    "givenName": "Sentry Support",
                    "emailAddress": "support@getsentry.com"
                },
                "support": {
                    "givenName": "Sentry Support",
                    "emailAddress": "support@getsentry.com"
                }
            },
            "organization": {
                "en-US": {
                    "name": "sentry",
                    "displayname": "Sentry",
                    "url": "https://www.getsentry.com"
                }
            },
        }

    def prepare_saml_request(self, request):
        return {
            'http_host': request.META['HTTP_HOST'],
            'script_name': request.META['PATH_INFO'],
            'server_port': request.META['SERVER_PORT'],
            'get_data': request.GET.copy(),
            'post_data': request.POST.copy()
        }

    def build_auth(self, request, config):
        req = self.prepare_saml_request(request)
        return OneLogin_Saml2_Auth(req, config)


class SamlRequest(AuthView, SamlMixin):
    def __init__(self, config):
        self.config = config

    def dispatch(self, request, provider):
        auth = self.build_auth(request, self.config)
        redirect_uri = absolute_uri(self.get_next_url())
        return self.redirect(auth.login(redirect_uri))


class SamlAcs(AuthView, SamlMixin):
    def __init__(self, config):
        self.config = config

    def dispatch(self, request, provider):
        auth = self.build_auth(request, self.config)
        auth.process_response()
        errors = auth.get_errors()
        if errors:
            self.logger.info('Failed to authenticate: %s', ', '.join(errors))
            return self.error(request, provider, ERR_ACS_FAILURE)

        if not auth.is_authenticated():
            # TODO(dcramer): im not entirely sure what we should do regarding thiscase
            return self.error(request, provider, ERR_ACS_FAILURE)
        self.bind_state(request, 'data', auth.get_attributes())

        # XXX: RelayState gets set how? where? to what? is this what we passed in login() ?
        if 'RelayState' in req['post_data'] and OneLogin_Saml2_Utils.get_self_url(req) != req['post_data']['RelayState']:
            return self.redirect(auth.redirect_to(req['post_data']['RelayState']))
        return self.next_step()


class OneLoginProvider(Provider, SamlMixin):
    def __init__(self, connector_id=None, connector_cert=None, **config):
        self.connector_id = connector_id
        self.connector_cert = connector_cert
        super(Provider, self).__init__(**config)

    def get_auth_pipeline(self):
        config = self.build_config(
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

    def get_identity(self, state):
        user_data = state['data']
        return {
            # TODO: is there a "correct" email?
            'email': None,
            'name': None,
        }