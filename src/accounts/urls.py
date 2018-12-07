from django.conf.urls import url, include
from rest_framework.urlpatterns import format_suffix_patterns
from rest_auth import views as rest_auth_views
from . import views as local_views


urlpatterns = [
    url(r'^accounts/password/reset/$', rest_auth_views.PasswordResetView.as_view(), name='password_reset'),
    url(r'^accounts/password/reset/confirm/(?P<uidb64>[0-9A-Za-z]+)-(?P<token>.+)/$', rest_auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),

	# Local views
    url(r'^accounts/profile/$', local_views.UserProfileView.as_view(), name='user_profile'),
    url(r'^accounts/profile/change/$', local_views.UpdateProfileView.as_view(), name='change_user_profile'),
    url(r'^accounts/profile/delete/$', local_views.DeleteProfileView.as_view(), name='delete_profile'),
    url(r'^accounts/profile/delete/(?P<pk>[^/]+)', local_views.DeleteProfileView.as_view(), name='delete_profile'),
    url(r'^accounts/register/$', local_views.RegistrationView.as_view(), name='register'),
    url(r'^accounts/activate/(?P<pk>[^/]+)', local_views.ActivateViews.as_view(), name='activate'),
    url(r'^accounts/resend-activation-link/$', local_views.resend_activation_link, name='resend_activation_link'),
    url(r'^accounts/facebook/$', local_views.FacebookLogin.as_view(), name='fb_login'),
    url(r'^accounts/twitter/$', local_views.TwitterLogin.as_view(), name='twitter_login'),
    url(r'^accounts/google/$', local_views.GoogleLogin.as_view(), name='google_login'),

    url(r'^accounts/twitter-token/$', local_views.getTwitterReqToken.as_view(), name='twitter--req-token'),
    url(r'^accounts/twitter-access-token/$', local_views.getTwitterAccToken.as_view(), name='twitter-acc-token'),

    # Django Rest Auth

    url(r'^accounts/login/$', rest_auth_views.LoginView.as_view(), name='rest_login'),
    url(r'^accounts/logout/$', rest_auth_views.LogoutView.as_view(), name='rest_logout'),
    url(r'^accounts/user/$', local_views.UserProfileView.as_view(), name='user_details'),
    url(r'^accounts/password/change/$', rest_auth_views.PasswordChangeView.as_view(), name='rest_password_change'),

    url(r'^accounts/users/$', local_views.GetUsersView.as_view(), name='get_users'),
    url(r'^accounts/user_items/$', local_views.GetUserItemCounts.as_view({'get': 'list'}), name='get_user_items'),

    url(r'^test-template/', local_views.test_template, name="test template"),

    url(r'^/', include('allauth.urls')),
]

urlpatterns = format_suffix_patterns(urlpatterns)
