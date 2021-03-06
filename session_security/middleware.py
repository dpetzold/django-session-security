import datetime
import logging

from django import http
from django.contrib.auth import logout

from settings import *

logger = logging.getLogger(__name__)



class SessionSecurityMiddleware(object):
    """
    The heart of the security that this application attemps to provide.

    To install this middleware, add to your ``settings.MIDDLEWARE_CLASSES``::

        'session_security.middleware.SessionSecurityMiddleware'

    Make sure that it is placed **after** authentication middlewares.
    """

    def process_request(self, request):
        """
        Set up ``request.session['session_security']`` if unset, logout and
        redirect the user to ``LOGIN_URL?next=/the/path/`` if his session has
        expired.

        - If the user is not authenticated: do nothing.
        - If the request url is in ``PASSIVE_URLS``: do nothing.
        - If ``request.session['session_security']`` is unset: set it up.
        - If the seconds elapsed since
          ``request.session['session_security']['last_activity']`` exceeds
          ``EXPIRE_AFTER``:
            - Logout the user,
            - Redirect to ``LOGIN_URL?next=/the/path/``.
        - Otherwise: update
          ``request.session['session_security']['last_activity']`` to now.
        """
        if not request.user.is_authenticated():
            return

        if request.profile is None:
            return

        if request.profile.caregiver is None:
            return

        if request.path in PASSIVE_URLS:
            return

        now = datetime.datetime.now()
        expire_after = request.agency.caregiver_auto_logout_time * 60
        if expire_after == 0:
            return

        data = request.session.get('session_security', {
            'LOGOUT_URL': LOGOUT_URL,
            'LOGIN_URL': LOGIN_URL,
            'EXPIRE_AFTER': expire_after,
            'WARN_AFTER': WARN_AFTER,
            'last_activity': now,
        })

        delta = now - data['last_activity']

        if delta.seconds > expire_after and request.path_info != LOGIN_URL:
            logger.info('Logged %s out after %s' % (request.user, delta))
            logout(request)
            return http.HttpResponseRedirect(
                '%s?next=%s' % (LOGIN_URL, request.path_info))

        data['last_activity'] = now
        request.session['session_security'] = data
