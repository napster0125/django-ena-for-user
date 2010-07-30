from django.test import TestCase
from django.contrib.auth.models import User
from django.conf import settings

from userena.utils import get_gravatar, signin_redirect
from userena import settings as userena_settings


import hashlib

class UtilsTests(TestCase):
    """ Test the extra utils methods """
    fixtures = ['users']

    def test_get_gravatar(self):
        template = 'http://www.gravatar.com/avatar/%(hash)s?s=%(size)s&d=%(type)s'

        # The hash for alice@example.com
        hash = hashlib.md5('alice@example.com').hexdigest()

        # Check the defaults.
        self.failUnlessEqual(get_gravatar('alice@example.com'),
                             template % {'hash': hash,
                                         'size': 80,
                                         'type': 'identicon'})

        # Check different size
        self.failUnlessEqual(get_gravatar('alice@example.com', size=200),
                             template % {'hash': hash,
                                         'size': 200,
                                         'type': 'identicon'})

        # Check different default
        http_404 = get_gravatar('alice@example.com', default='404')
        self.failUnlessEqual(http_404,
                             template % {'hash': hash,
                                         'size': 80,
                                         'type': '404'})

        # Is it really a 404?
        response = self.client.get(http_404)
        self.failUnlessEqual(response.status_code, 404)

        # Test the switch to HTTPS
        userena_settings.USERENA_USE_HTTPS = True

        template = 'https://secure.gravatar.com/avatar/%(hash)s?s=%(size)s&d=%(type)s'
        self.failUnlessEqual(get_gravatar('alice@example.com'),
                             template % {'hash': hash,
                                         'size': 80,
                                         'type': 'identicon'})

        # And set back to default
        userena_settings.USERENA_USE_HTTPS = False

    def test_signin_redirect(self):
        """
        Test redirect function which should redirect the user after a
        succesfull signin.

        """
        # Test with a requested redirect
        self.failUnlessEqual(signin_redirect(redirect='/accounts/'), '/accounts/')

        # Test with only the user specified
        user = User.objects.get(pk=1)
        self.failUnlessEqual(signin_redirect(user=user),
                             user.account.get_absolute_url())

        # The ultimate fallback, probably never used
        self.failUnlessEqual(signin_redirect(), settings.LOGIN_REDIRECT_URL)
