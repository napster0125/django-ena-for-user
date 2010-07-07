from django.test import TestCase
from django.contrib.auth.models import User
from django.core import mail
from django.core.urlresolvers import reverse
from django.contrib.sites.models import Site

from userina.models import Account
from userina import settings as userina_settings

import re

class AccountModelTests(TestCase):
    """ Test the model and manager of Account """
    user_username = 'alice'
    user_password= 'swordfish'
    user_email = 'alice@example.com'

    user_info = {'username': 'alice',
                 'password': 'swordfish',
                 'email': 'alice@example.com'}

    fixtures = ['users.json', 'accounts.json']

    def test_age_property(self):
        """ Test if the ``user.age`` returns the correct age. """
        account = Account.objects.get(pk=1)
        self.assertEqual(account.age, 27)

    def test_get_account(self):
        """
        Test if ``user.account`` always returns the account for the user.

        """
        user_with_account = User.objects.get(pk=1)
        user_without_account = User.objects.get(pk=2)

        # Account should be the account model for a user who already has an
        # account.
        self.assertEqual(type(user_with_account.account), Account)

        # Account should be created when a user has no account
        self.assertEqual(type(user_without_account.account), Account)

    def test_create_user(self):
        """
        Test the creation of a new user.

        ``Account.create_user`` should create a new user that is set to active.
        It should also create a new account for this user.

        """
        new_user = Account.objects.create_user(**self.user_info)
        self.assertEqual(new_user.username, self.user_info['username'])
        self.assertEqual(new_user.email, self.user_info['email'])
        self.failUnless(new_user.check_password(self.user_info['password']))
        self.failUnless(new_user.is_active)
        self.failUnlessEqual(Account.objects.filter(user__email=self.user_info['email']).count(), 1)

    def test_verification_email(self):
        """
        When a new account is created, a verification e-mail should be send out
        by ``Account.send_verification_email``.

        """
        new_user = Account.objects.create_user(**self.user_info)
        self.failUnlessEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [self.user_email])

    def test_create_account(self):
        """
        Test the creation of a new account.

        ``Account.objects.create_account`` should create a new account for this user.
        The user is not verified yet therefore should get an e-mail which
        contains the ``verification_key``.

        """
        new_user = User.objects.create_user(**self.user_info)
        new_account = Account.objects.create_account(new_user)

        self.assertEqual(Account.objects.filter(user__email=self.user_info['email']).count(), 1)
        self.assertEqual(new_account.user.id, new_user.id)
        self.failUnless(re.match('^[a-f0-9]{40}$', new_account.verification_key))

    def test_get_verification_url(self):
        """
        Test the verification URL that is created by
        ``Account.get_verification_url``.

        """
        account = Account.objects.create_user(**self.user_info).account
        site = Site.objects.get_current()

        verification_url = 'http://%(domain)s%(path)s' % {'domain': site.domain,
                                                           'path': reverse('userina_verify',
                                                                           kwargs={'verification_key': account.verification_key})}
        self.failUnlessEqual(account.get_verification_url, verification_url)

    def test_verification_valid(self):
        account = Account.objects.create_user(**self.user_info).account

        verified_account = Account.objects.verify_account(account.verification_key)

        # The returned account should be the same as the one just created.
        self.failUnlessEqual(account, verified_account)

        # The account should now be verified.
        self.failIf(verified_account.is_verified)

        # The verification key should be the same as in the settings
        self.assertEqual(account.verification_key, userina_settings.USERINA_VERIFIED)

    def test_verification_invalid(self):
        pass

    def test_verification_expired(self):
        pass
