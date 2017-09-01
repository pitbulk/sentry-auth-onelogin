from __future__ import absolute_import, print_function

from django import forms
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.core.validators import URLValidator
from django.utils.translation import ugettext_lazy as _

from onelogin.saml2.idp_metadata_parser import OneLogin_Saml2_IdPMetadataParser

from sentry.auth.view import AuthView
from sentry.auth.providers.saml2 import SAML2Provider, SAML2ConfigureView, NAMEID_FORMAT_CHOICES, AUTHNCONTEXT_CHOICES
from sentry.utils.http import absolute_uri

from .constants import ONELOGIN_METADATA_URL_PREFIX


class OneLoginSAMLForm(forms.Form):
    idp_entityid = forms.CharField(label='OneLogin Entity ID', help_text="Issuer URL")
    idp_sso_url = forms.URLField(label='OneLogin Single Sign On URL', help_text="SAML 2.0 Endpoint (HTTP)")
    idp_slo_url = forms.URLField(label='OneLogin Single Log Out URL', required=False, help_text="SLO Endpoint (HTTP)")
    idp_x509cert = forms.CharField(label='OneLogin x509 public certificate', widget=forms.Textarea, help_text="X.509 Certificate")


class OneLoginAdvancedForm(forms.Form):
    advanced_spentityid = forms.CharField(label='SP EntityID', required=False, help_text=_('Service Provider EntityID, if not provided, the URL where Sentry publish the SP metadata will be used as its value'))
    advanced_nameidformat = forms.ChoiceField(label='NameID Format', required=False, choices=NAMEID_FORMAT_CHOICES, help_text=_('Specifies constraints on the name identifier to be used to represent the requested subject. Review OneLogin metadata to see the supported NameID formats'))
    advanced_requestedauthncontext = forms.MultipleChoiceField(label='Requested Authn Context', required=False, choices=AUTHNCONTEXT_CHOICES, help_text=_('AuthContext sent in the AuthNRequest. You can select none (any authn source will be accepted), one or multiple values'))
    advanced_sp_x509cert = forms.CharField(label='SP X.509 Certificate', widget=forms.Textarea, required=False, help_text=_('Public x509 certificate of the Service Provider'))
    advanced_sp_privatekey = forms.CharField(label='SP Private Key', widget=forms.Textarea, required=False, help_text=_('Private Key of the Service Provider'))

    def clean(self):
        super(OneLoginAdvancedForm, self).clean()

        requires_sp_cert_data_due_enc = self.data.get('advanced_want_assertion_encrypted', False)
        has_sp_cert_data = self.data.get('advanced_sp_x509cert', None) and self.data.get('advanced_sp_privatekey', None)

        if requires_sp_cert_data_due_enc and not has_sp_cert_data:
            self._errors["advanced_sp_x509cert"] = [_("Required in order to be provided to OneLogin to let it encrypt")]
            self._errors["advanced_sp_privatekey"] = [_("Required in order to decrypt SAML data from OneLogin")]
            del self.cleaned_data["advanced_sp_x509cert"]
            del self.cleaned_data["advanced_sp_privatekey"]
        return self.cleaned_data


class OneLoginSAML2ConfigureView(SAML2ConfigureView):
    saml_form_cls = OneLoginSAMLForm
    advanced_form_cls = OneLoginAdvancedForm

    def display_configure_view(self, organization, saml_form, options_form, attr_mapping_form, advanced_form):
        sp_metadata_url = absolute_uri(reverse('sentry-auth-organization-saml-metadata', args=[organization.slug]))

        return self.render('sentry_auth_onelogin/configure.html', {
            'sp_metadata_url': sp_metadata_url,
            'saml_form': saml_form,
            'options_form': options_form,
            'attr_mapping_form': attr_mapping_form,
            'advanced_form': advanced_form
        })


class OneLoginSelectIdP(AuthView):
    def handle(self, request, helper):
        missing_values = error_value = error_url = False
        id_or_metadata_url = url = ''
        if 'action_save' in request.POST:
            id_or_metadata_url = request.POST['id_or_metadata_url']

            # Get metadata url if an app_id was provided
            if id_or_metadata_url and id_or_metadata_url.isdigit():
                id_or_metadata_url = ONELOGIN_METADATA_URL_PREFIX + id_or_metadata_url

            validate_url = URLValidator()
            try:
                validate_url(id_or_metadata_url)
                url = id_or_metadata_url
                try:
                    data = OneLogin_Saml2_IdPMetadataParser.parse_remote(url)

                    if data and 'idp' in data:
                        idp_data = SAML2Provider.extract_idp_data_from_parsed_data(data)
                        form2 = OneLoginSAMLForm(idp_data)
                        if form2.is_valid():
                            helper.bind_state('idp', idp_data)
                            helper.bind_state('contact', request.user.email)
                            return helper.next_step()
                        else:
                            missing_values = form2.errors.keys
                except Exception:
                    error_url = True
            except ValidationError:
                error_value = True

        return self.respond('sentry_auth_onelogin/select-idp.html', {
            'error_value': error_value,
            'error_url': error_url,
            'missing_values': missing_values,
            'id_or_metadata_url': id_or_metadata_url
        })
