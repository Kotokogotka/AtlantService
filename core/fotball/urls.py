from django.urls import path
from .views import LoginApiView, UserInfoApiView, LogOutApiView, TestView


urlpatterns = [
    path('api/test/', TestView.as_view(), name='api-test'),
    path('api/login/', LoginApiView.as_view(), name='api-login'),
    path('api/user-info/', UserInfoApiView.as_view(), name='api-user-info'),
    path('api/logout/', LogOutApiView.as_view(), name='api-logout'),
]