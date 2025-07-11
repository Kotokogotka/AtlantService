from django.urls import path
from .views import LoginApiView


urlpatterns = [
    path('api/login/', LoginApiView.as_view(), name='api-login'),
]