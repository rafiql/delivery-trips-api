from django.conf.urls import url, include
from rest_framework.routers import SimpleRouter
from rest_framework_jwt import views as jwt
from apps.user.views import PasswordLogin, SalesManagerSignup


router = SimpleRouter()
app_name = 'user'


urlpatterns = [
    url(r'^api/token/refresh/$', jwt.refresh_jwt_token),
    url(r'^api/token/verify/$', jwt.verify_jwt_token),
    url(r'^api/token/$', jwt.obtain_jwt_token, name='get_jwt_token'),

    url(r'^login/password/$', PasswordLogin.as_view()),
    url(r'^api/signup_sales/$', SalesManagerSignup.as_view()),
    url(r'^api/signup_sales/(?P<pk>[0-9]+)$', SalesManagerSignup.as_view()),
    # url(r'^api/', include(router.urls), name='api'),
    # url(r'^api/username/$', login_view.get_username, name='get_username'),
    # url(r'^api/username-availability/$', login_view.check_username_availability, name='username_availability'),

    # url(r'^api/update_password/$', api.update_password),
]