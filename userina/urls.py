from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template

from userina import views as userina_views

urlpatterns = patterns('',
                       # Activate
                       url(r'^activate/complete/$',
                           direct_to_template,
                           {'template': 'userina/activation_complete.html'},
                           name='userina_activation_complete'),
                       url(r'^activate/(?P<activation_key>\w+)/$',
                           userina_views.activate,
                           name='userina_activate'),

                       # Signin, signout and signup
                       url(r'^signin/$',
                           userina_views.signin,
                           name='userina_signin'),
                       url(r'^signout/$',
                           userina_views.signout,
                           name='userina_signout'),
                       url(r'^signup/$',
                           userina_views.signup,
                           name='userina_signup'),
                       url(r'^signup/complete/$',
                           direct_to_template,
                           {'template': 'userina/signup_complete.html'},
                           name='userina_signup_complete'),

                       # Forgot password
                       url(r'^password/reset/$',
                           userina_views.password_reset,
                           name='userina_password_reset'),
                       url(r'^password/reset/confirm/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/$',
                           userina_views.password_reset_confirm,
                           name='userina_password_reset_confirm'),
                       url(r'^password/reset/complete/$',
                           direct_to_template,
                           {'template': 'userina/password_reset_complete.html'}),

                       # Account settings
                       url(r'^password/$',
                           userina_views.password_change,
                           name='userina_password_change'),
                       url(r'^password/complete/$',
                           direct_to_template,
                           {'template': 'userina_password_complete.html'},
                           name='userina_password_complete'),
                       url(r'/$',
                           userina_views.detail,
                           name='userina_detail'),
)
