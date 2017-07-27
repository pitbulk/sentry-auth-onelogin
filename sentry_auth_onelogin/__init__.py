from __future__ import absolute_import

from sentry.auth import register

from .provider import OneloginSAML2Provider

register('onelogin', OneloginSAML2Provider)
