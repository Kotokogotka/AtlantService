from django.urls import path
from .views import (
    LoginApiView, UserInfoApiView, LogOutApiView, TestView, 
    TrainerGroupsApiView, GroupDetailApiView, TrainerAttendanceApiView, 
    GroupAttendanceApiView, AttendanceHistoryApiView, ParentChildInfoApiView,
    ParentAttendanceApiView, ParentNextTrainingApiView, ParentCommentsApiView,
    ParentPaymentCalculationApiView, ParentMedicalCertificatesApiView, AdminMedicalCertificatesApiView,
    AdminApproveMedicalCertificateApiView, AdminRejectMedicalCertificateApiView,
    AdminScheduleApiView, ScheduleApiView, TrainerCommentsApiView, ScheduleNotificationsApiView, MarkNotificationReadApiView,
    PaymentInvoicesApiView, GenerateInvoiceApiView, PaymentSettingsApiView, TrainingCancellationNotificationsApiView, AdminAttendanceApiView, AdminGroupChildrenApiView, AdminAttendanceTableApiView
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
    path('api/trainer/comments/', TrainerCommentsApiView.as_view(), name='api-trainer-comments'),
    # Parent API endpoints
    path('api/parent/child-info/', ParentChildInfoApiView.as_view(), name='api-parent-child-info'),
    path('api/parent/attendance/', ParentAttendanceApiView.as_view(), name='api-parent-attendance'),
    path('api/parent/next-training/', ParentNextTrainingApiView.as_view(), name='api-parent-next-training'),
    path('api/parent/comments/', ParentCommentsApiView.as_view(), name='api-parent-comments'),
    path('api/parent/payment-calculation/', ParentPaymentCalculationApiView.as_view(), name='api-parent-payment-calculation'),
    path('api/parent/medical-certificates/', ParentMedicalCertificatesApiView.as_view(), name='api-parent-medical-certificates'),
    # Admin API endpoints
    path('api/admin/medical-certificates/', AdminMedicalCertificatesApiView.as_view(), name='api-admin-medical-certificates'),
    path('api/admin/medical-certificates/<int:certificate_id>/approve/', AdminApproveMedicalCertificateApiView.as_view(), name='api-admin-approve-certificate'),
    path('api/admin/medical-certificates/<int:certificate_id>/reject/', AdminRejectMedicalCertificateApiView.as_view(), name='api-admin-reject-certificate'),
    path('api/admin/schedule/', AdminScheduleApiView.as_view(), name='api-admin-schedule'),
    path('api/admin/schedule/<int:training_id>/', AdminScheduleApiView.as_view(), name='api-admin-schedule-detail'),
    # Schedule API endpoints (для всех ролей)
    path('api/schedule/', ScheduleApiView.as_view(), name='api-schedule'),
    path('api/schedule/notifications/', ScheduleNotificationsApiView.as_view(), name='api-schedule-notifications'),
    path('api/schedule/notifications/<int:notification_id>/read/', MarkNotificationReadApiView.as_view(), name='api-mark-notification-read'),
    # Payment API endpoints
    path('api/parent/invoices/', PaymentInvoicesApiView.as_view(), name='api-parent-invoices'),
    path('api/admin/generate-invoices/', GenerateInvoiceApiView.as_view(), name='api-admin-generate-invoices'),
    path('api/admin/payment-settings/', PaymentSettingsApiView.as_view(), name='api-admin-payment-settings'),
    path('api/training-cancellation-notifications/', TrainingCancellationNotificationsApiView.as_view(), name='api-training-cancellation-notifications'),
    path('api/admin/attendance/', AdminAttendanceApiView.as_view(), name='api-admin-attendance'),
    path('api/admin/attendance-table/', AdminAttendanceTableApiView.as_view(), name='api-admin-attendance-table'),
    path('api/admin/group-children/', AdminGroupChildrenApiView.as_view(), name='api-admin-group-children'),
]