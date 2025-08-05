from django.urls import path
from .views import (
    LoginApiView, UserInfoApiView, LogOutApiView, TestView, 
    TrainerGroupsApiView, GroupDetailApiView, TrainerAttendanceApiView, 
    GroupAttendanceApiView, AttendanceHistoryApiView
)


urlpatterns = [
    path('api/test/', TestView.as_view(), name='api-test'),
    path('api/login/', LoginApiView.as_view(), name='api-login'),
    path('api/user-info/', UserInfoApiView.as_view(), name='api-user-info'),
    path('api/logout/', LogOutApiView.as_view(), name='api-logout'),
    path('api/trainer/groups/', TrainerGroupsApiView.as_view(), name='api-trainer-groups'),
    path('api/trainer/group/<int:group_id>/', GroupDetailApiView.as_view(), name='api-group-detail'),
    path('api/trainer/attendance/', TrainerAttendanceApiView.as_view(), name='api-trainer-attendance'),
    path('api/trainer/attendance/group/<int:group_id>/', GroupAttendanceApiView.as_view(), name='api-group-attendance'),
    path('api/trainer/attendance/history/<int:group_id>/', AttendanceHistoryApiView.as_view(), name='api-attendance-history'),
]