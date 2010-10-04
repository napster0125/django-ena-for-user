from django.core.management.base import NoArgsCommand

from userena.models import UserenaSignup
from optparse import make_option

class Command(NoArgsCommand):
    """
    Search for users that still haven't verified their e-mail address after
    ``USERENA_ACTIVATION_DAYS`` and delete them.

    """
    help = 'Deletes expired users.'
    def handle_noargs(self, **options):
        users = UserenaSignup.objects.delete_expired_users()
