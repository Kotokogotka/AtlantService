from django.contrib import admin
from django.utils.html import format_html
from .models import Child, Trainer, GroupKidGarden, Attendance, User, Parent, TrainingRate, MedicalCertificate, TrainingSchedule, TrainerComment, ScheduleChangeNotification, NotificationRead


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'role', 'linked_trainer', 'linked_child')
    list_filter = ('role',)
    search_fields = ('username',)
    readonly_fields = ('password',)
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('username', 'password', 'role')
        }),
        ('Связи', {
            'fields': ('linked_trainer', 'linked_child'),
            'classes': ('collapse',)
        }),
    )



@admin.register(Trainer)
class TrainerAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'phone', 'work_space', 'get_groups_count')
    search_fields = ('full_name', 'phone', 'work_space')
    list_filter = ('groups__kindergarten_number',)
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('full_name', 'phone', 'work_space')
        }),
        ('Группы', {
            'fields': ('groups',),
            'classes': ('collapse',)
        }),
    )
    
    filter_horizontal = ('groups',)
    
    def get_groups_count(self, obj):
        return obj.groups.count()
    get_groups_count.short_description = 'Количество групп'


@admin.register(GroupKidGarden)
class GroupKidGardenAdmin(admin.ModelAdmin):
    list_display = ('name', 'kindergarten_number', 'age_level', 'get_trainers')
    list_filter = ('age_level', 'kindergarten_number')
    search_fields = ('name', 'kindergarten_number')
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'kindergarten_number', 'age_level')
        }),
    )
    
    def get_trainers(self, obj):
        trainers = obj.trainers.all()
        if trainers:
            return ', '.join([trainer.full_name for trainer in trainers])
        return 'Не назначены'
    get_trainers.short_description = 'Тренеры'


@admin.register(Parent)
class ParentAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'phone', 'get_children_count')
    search_fields = ('full_name', 'phone')
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('full_name', 'phone')
        }),
        ('Дети', {
            'fields': ('children',),
            'classes': ('collapse',)
        }),
    )
    
    filter_horizontal = ('children',)
    
    def get_children_count(self, obj):
        return obj.children.count()
    get_children_count.short_description = 'Количество детей'

    


@admin.register(Child)
class ChildAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'birth_date', 'parent_name', 'group', 'is_active')
    list_filter = ('is_active', 'group', 'birth_date')
    search_fields = ('full_name', 'parent_name__full_name')
    date_hierarchy = 'birth_date'
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('full_name', 'birth_date', 'is_active')
        }),
        ('Связи', {
            'fields': ('parent_name', 'group'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('child', 'group', 'date', 'status', 'reason_short')
    list_filter = ('status', 'date', 'group', 'child')
    search_fields = ('child__full_name', 'reason')
    date_hierarchy = 'date'
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('child', 'group', 'date', 'status')
        }),
        ('Дополнительно', {
            'fields': ('reason',),
            'classes': ('collapse',)
        }),
    )
    
    def reason_short(self, obj):
        if obj.reason:
            return obj.reason[:50] + '...' if len(obj.reason) > 50 else obj.reason
        return '-'
    reason_short.short_description = 'Причина'


@admin.register(TrainingRate)
class TrainingRateAdmin(admin.ModelAdmin):
    list_display = ('group', 'price', 'active_form')
    list_filter = ('active_form', 'group')
    search_fields = ('group__name',)
    date_hierarchy = 'active_form'
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('group', 'price', 'active_form')
        }),
    )


@admin.register(MedicalCertificate)
class MedicalCertificateAdmin(admin.ModelAdmin):
    list_display = ('child', 'parent', 'date_from', 'date_to', 'status', 'total_cost', 'uploaded_at')
    list_filter = ('status', 'uploaded_at', 'date_from', 'date_to')
    search_fields = ('child__full_name', 'parent__username', 'note', 'absence_reason')
    date_hierarchy = 'uploaded_at'
    readonly_fields = ('uploaded_at', 'total_cost')
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('child', 'parent', 'certificate_file', 'date_from', 'date_to')
        }),
        ('Детали справки', {
            'fields': ('note', 'absence_reason'),
            'classes': ('collapse',)
        }),
        ('Финансовая информация', {
            'fields': ('cost_per_lesson', 'total_cost'),
            'classes': ('collapse',)
        }),
        ('Статус и комментарии', {
            'fields': ('status', 'admin_comment'),
            'classes': ('collapse',)
        }),
        ('Системная информация', {
            'fields': ('uploaded_at',),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('child', 'parent')


@admin.register(TrainingSchedule)
class TrainingScheduleAdmin(admin.ModelAdmin):
    list_display = ('group', 'date', 'time', 'trainer', 'status', 'created_by', 'created_at')
    list_filter = ('status', 'date', 'group', 'trainer', 'created_at')
    search_fields = ('group__name', 'trainer__full_name', 'location', 'notes')
    date_hierarchy = 'date'
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('group', 'trainer', 'date', 'time', 'duration_minutes')
        }),
        ('Дополнительно', {
            'fields': ('location', 'status', 'notes'),
            'classes': ('collapse',)
        }),
        ('Системная информация', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('group', 'trainer', 'created_by')


@admin.register(TrainerComment)
class TrainerCommentAdmin(admin.ModelAdmin):
    list_display = ('trainer', 'child', 'comment_preview', 'created_at')
    list_filter = ('trainer', 'created_at')
    search_fields = ('trainer__full_name', 'child__full_name', 'comment_text')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('trainer', 'child', 'comment_text')
        }),
        ('Временные метки', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def comment_preview(self, obj):
        return obj.comment_text[:50] + '...' if len(obj.comment_text) > 50 else obj.comment_text
    comment_preview.short_description = 'Комментарий'


@admin.register(ScheduleChangeNotification)
class ScheduleChangeNotificationAdmin(admin.ModelAdmin):
    list_display = ('training', 'notification_type', 'message_preview', 'created_by', 'created_at', 'is_read_by_trainer')
    list_filter = ('notification_type', 'created_at', 'is_read_by_trainer')
    search_fields = ('training__group__name', 'message', 'created_by__username')
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('training', 'notification_type', 'message', 'created_by')
        }),
        ('Изменения', {
            'fields': ('old_date', 'new_date', 'old_time', 'new_time'),
            'classes': ('collapse',)
        }),
        ('Статус', {
            'fields': ('is_read_by_trainer', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    def message_preview(self, obj):
        return obj.message[:50] + '...' if len(obj.message) > 50 else obj.message
    message_preview.short_description = 'Сообщение'


@admin.register(NotificationRead)
class NotificationReadAdmin(admin.ModelAdmin):
    list_display = ('user', 'notification_preview', 'read_at')
    list_filter = ('read_at',)
    search_fields = ('user__username', 'notification__message')
    readonly_fields = ('read_at',)
    
    def notification_preview(self, obj):
        return f"{obj.notification.training.group.name} - {obj.notification.get_notification_type_display()}"
    notification_preview.short_description = 'Уведомление'

