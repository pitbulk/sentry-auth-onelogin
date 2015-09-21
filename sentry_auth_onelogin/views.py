from __future__ import absolute_import, print_function

from django import forms
from django.conf import settings
from sentry.auth import AuthView, Provider

from .mixins import SamlMixin

from onelogin.saml2.auth import OneLogin_Saml2_Auth
from onelogin.saml2.settings import OneLogin_Saml2_Settings
from onelogin.saml2.utils import OneLogin_Saml2_Utils


ERR_ACS_FAILURE = 'There was an error authenticating you with the provider.'


class SamlSettingsForm(forms.Form):
    pass



class SamlAcs(AuthView, SamlMixin):
    def __init__(self, config):
        self.config = config


class SamlConfigure(AuthView, SamlMixin):
    def __init__(self, config):
        self.config = config

    def handle(self, request, helper):
        access_token = helper.fetch_state('data')['access_token']
        org_list = self.client.get_org_list(access_token)

        form = ConfigureForm(org_list, request.POST or None)
        if form.is_valid():
            org_id = form.cleaned_data['org']
            org = [o for o in org_list if org_id == str(o['id'])][0]
            helper.bind_state('org', org)
            return helper.next_step()

        return self.respond('sentry_auth_onelogin/configure.html', {
            'form': form,
            'org_list': org_list,
        })


class SamlRequest(AuthView, SamlMixin):
    def __init__(self, config):
        self.config = config

    def handle(self, request, helper):
        auth = self.build_auth(request, self.config)
        redirect_uri = absolute_uri(self.get_next_url())
        return self.redirect(auth.login(redirect_uri))
