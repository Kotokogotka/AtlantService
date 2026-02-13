from django.contrib import admin
from django import forms
from django.contrib.auth.hashers import make_password
from django.utils.html import format_html
from .models import Child, Trainer, GroupKidGarden, Attendance, User, Parent, TrainingRate, MedicalCertificate, TrainingSchedule, TrainerComment, ScheduleChangeNotification, NotificationRead, PaymentSettings, GlobalPaymentQR, PaymentInvoice, PaymentReceipt, TrainingCancellationNotification


class SafeFkM2MAdminMixin:
    """
    Миксин для всех админок: перед сохранением «чистим» FK (если ссылка не существует — в null),
    при сохранении M2M выставляем только существующие id. Устраняет IntegrityError при popup/пустой БД.
    Также отключаем запись в django_admin_log (LogEntry), т.к. там FK на auth.User, а в админке
    залогинен fotball.User — иначе при сохранении любой сущности получаем FOREIGN KEY constraint failed.
    """
    def log_addition(self, request, object, message):
        pass  # LogEntry.user_id → auth.User; request.user — fotball.User → IntegrityError

    def log_change(self, request, object, message):
        pass

    def log_deletion(self, request, object, object_repr):
        pass

    def save_model(self, request, obj, form, change):
        model = obj._meta.model
        for f in model._meta.get_fields():
            if not (f.many_to_one and f.concrete) and not (f.one_to_one and f.concrete):
                continue
            if not getattr(f, 'attname', None):
                continue
            pk = getattr(obj, f.attname, None)
            if pk is None or pk == '' or (isinstance(pk, (int, float)) and pk == 0):
                if getattr(f, 'null', False):
                    setattr(obj, f.attname, None)
                continue
            try:
                pk = int(pk)
            except (TypeError, ValueError):
                if getattr(f, 'null', False):
                    setattr(obj, f.attname, None)
                continue
            related_model = getattr(f, 'related_model', None)
            if not related_model or not related_model.objects.filter(pk=pk).exists():
                if getattr(f, 'null', False):
                    setattr(obj, f.attname, None)
        super().save_model(request, obj, form, change)

    def save_related(self, request, form, formsets, change):
        def safe_save_m2m():
            obj = form.instance
            for f in obj._meta.many_to_many:
                if f.name not in form.cleaned_data:
                    continue
                related_model = f.related_model
                values = form.cleaned_data[f.name]
                if values is None:
                    getattr(obj, f.name).clear()
                    continue
                pks = [getattr(x, 'pk', x) for x in values]
                existing = list(related_model.objects.filter(pk__in=pks).values_list('pk', flat=True))
                getattr(obj, f.name).set(existing)
        form.save_m2m = safe_save_m2m
        super().save_related(request, form, formsets, change)


class UserAdminForm(forms.ModelForm):
    """Форма с полем для ввода нового пароля (сохраняется в виде хэша)."""
    password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
        label='Пароль',
        help_text='Оставьте пустым, чтобы не менять. При вводе будет сохранён в зашифрованном виде.'
    )

    class Meta:
        model = User
        fields = ('username', 'password', 'role', 'linked_trainer', 'linked_child')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['password'].required = False
        else:
            self.fields['password'].required = True
            self.fields['password'].help_text = 'Обязательно при создании пользователя.'

    def save(self, commit=True):
        user = super().save(commit=False)
        new_password = self.cleaned_data.get('password')
        if new_password:
            user.password = make_password(new_password)
        if commit:
            user.save()
        return user


@admin.register(User)
class UserAdmin(SafeFkM2MAdminMixin, admin.ModelAdmin):
    form = UserAdminForm
    list_display = ('username', 'role', 'linked_trainer', 'linked_child')
    list_filter = ('role',)
    search_fields = ('username',)

    fieldsets = (
        ('Основная информация', {
            'fields': ('username', 'password', 'role')
        }),
        ('Связи', {
            'fields': ('linked_trainer', 'linked_child'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        # При создании сохраняем без FK — привязка trainer/child делается в model.save() через on_commit
        if not change:
            obj.linked_trainer_id = None
            obj.linked_child_id = None
        super().save_model(request, obj, form, change)



@admin.register(Trainer)
class TrainerAdmin(SafeFkM2MAdminMixin, admin.ModelAdmin):
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
class GroupKidGardenAdmin(SafeFkM2MAdminMixin, admin.ModelAdmin):
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
class ParentAdmin(SafeFkM2MAdminMixin, admin.ModelAdmin):
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
class ChildAdmin(SafeFkM2MAdminMixin, admin.ModelAdmin):
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
class AttendanceAdmin(SafeFkM2MAdminMixin, admin.ModelAdmin):
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
class TrainingRateAdmin(SafeFkM2MAdminMixin, admin.ModelAdmin):
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
class MedicalCertificateAdmin(SafeFkM2MAdminMixin, admin.ModelAdmin):
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
class TrainingScheduleAdmin(SafeFkM2MAdminMixin, admin.ModelAdmin):
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
class TrainerCommentAdmin(SafeFkM2MAdminMixin, admin.ModelAdmin):
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
class ScheduleChangeNotificationAdmin(SafeFkM2MAdminMixin, admin.ModelAdmin):
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
class NotificationReadAdmin(SafeFkM2MAdminMixin, admin.ModelAdmin):
    list_display = ('user', 'notification_preview', 'read_at')
    list_filter = ('read_at',)
    search_fields = ('user__username', 'notification__message')
    readonly_fields = ('read_at',)
    
    def notification_preview(self, obj):
        return f"{obj.notification.training.group.name} - {obj.notification.get_notification_type_display()}"
    notification_preview.short_description = 'Уведомление'


@admin.register(PaymentSettings)
class PaymentSettingsAdmin(SafeFkM2MAdminMixin, admin.ModelAdmin):
    list_display = ('kindergarten', 'price_per_training', 'default_trainings_per_month', 'invoice_generation_day', 'is_active')
    list_filter = ('is_active', 'created_at')
    search_fields = ('kindergarten__name', 'kindergarten__kindergarten_number')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('kindergarten', 'price_per_training', 'default_trainings_per_month')
        }),
        ('Настройки выставления счетов', {
            'fields': ('invoice_generation_day', 'is_active')
        }),
        ('Системная информация', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(GlobalPaymentQR)
class GlobalPaymentQRAdmin(SafeFkM2MAdminMixin, admin.ModelAdmin):
    list_display = ('id', 'has_qr_display')
    fields = ('qr_code',)
    verbose_name_plural = 'Общий QR для оплаты'

    def has_qr_display(self, obj):
        return 'Да' if obj and obj.qr_code else 'Нет'
    has_qr_display.short_description = 'QR загружен'

    def has_add_permission(self, request):
        return not GlobalPaymentQR.objects.exists()


@admin.register(PaymentInvoice)
class PaymentInvoiceAdmin(SafeFkM2MAdminMixin, admin.ModelAdmin):
    list_display = ('child', 'invoice_month_display', 'total_trainings', 'confirmed_absences', 'billable_trainings', 'total_amount', 'status', 'generated_at')
    list_filter = ('status', 'invoice_month', 'generated_at', 'child__group')
    search_fields = ('child__full_name', 'child__parent_name__full_name')
    readonly_fields = ('billable_trainings', 'total_amount', 'generated_at')
    date_hierarchy = 'invoice_month'
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('child', 'invoice_month', 'due_date')
        }),
        ('Расчет стоимости', {
            'fields': ('total_trainings', 'confirmed_absences', 'billable_trainings', 'price_per_training', 'total_amount')
        }),
        ('Статус оплаты', {
            'fields': ('status', 'paid_at', 'notes')
        }),
        ('QR для оплаты', {
            'fields': ('qr_code',),
            'description': 'Загрузите QR-код для оплаты по этому счёту (родитель увидит его в личном кабинете).'
        }),
        ('Системная информация', {
            'fields': ('generated_at',),
            'classes': ('collapse',)
        }),
    )
    
    def invoice_month_display(self, obj):
        months_ru = [
            'Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
            'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'
        ]
        return f"{months_ru[obj.invoice_month.month - 1]} {obj.invoice_month.year}"
    invoice_month_display.short_description = 'Месяц счета'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('child', 'child__group', 'child__parent_name')
    
    actions = ['mark_as_paid', 'mark_as_overdue']
    
    def mark_as_paid(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(status='paid', paid_at=timezone.now())
        self.message_user(request, f'Отмечено как оплачено: {updated} счетов.')
    mark_as_paid.short_description = 'Отметить как оплаченные'
    
    def mark_as_overdue(self, request, queryset):
        updated = queryset.update(status='overdue')
        self.message_user(request, f'Отмечено как просроченные: {updated} счетов.')
    mark_as_overdue.short_description = 'Отметить как просроченные'


@admin.register(PaymentReceipt)
class PaymentReceiptAdmin(SafeFkM2MAdminMixin, admin.ModelAdmin):
    list_display = ('id', 'invoice', 'uploaded_by', 'status', 'parsed_amount', 'amount_match', 'parsed_bank', 'created_at', 'reviewed_at')
    list_filter = ('status', 'amount_match', 'parsed_bank', 'created_at')
    search_fields = ('invoice__child__full_name', 'uploaded_by__username')
    readonly_fields = ('invoice', 'uploaded_by', 'receipt_file', 'created_at', 'reviewed_at', 'reviewed_by', 'parsed_amount', 'parsed_date', 'parsed_bank', 'amount_match', 'parsed_raw_preview')
    date_hierarchy = 'created_at'
    fieldsets = (
        (None, {'fields': ('invoice', 'uploaded_by', 'receipt_file', 'status', 'admin_comment')}),
        ('Распознанные данные с чека', {
            'fields': ('parsed_amount', 'parsed_date', 'parsed_bank', 'amount_match', 'parsed_raw_preview'),
            'description': 'Автоматически заполняется при загрузке. Сумма с чека сравнивается со счётом.'
        }),
        ('Проверка', {'fields': ('reviewed_at', 'reviewed_by')}),
        ('Даты', {'fields': ('created_at',)}),
    )


@admin.register(TrainingCancellationNotification)
class TrainingCancellationNotificationAdmin(SafeFkM2MAdminMixin, admin.ModelAdmin):
    list_display = ('group', 'cancelled_date', 'cancelled_time', 'reason_short', 'created_by', 'created_at', 'is_read_by_trainer', 'is_read_by_parents', 'affects_payment')
    list_filter = ('created_at', 'is_read_by_trainer', 'is_read_by_parents', 'affects_payment', 'group')
    search_fields = ('group__name', 'reason', 'created_by__username')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('group', 'cancelled_date', 'cancelled_time', 'reason')
        }),
        ('Статус прочтения', {
            'fields': ('is_read_by_trainer', 'is_read_by_parents', 'affects_payment')
        }),
        ('Системная информация', {
            'fields': ('created_by', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    def reason_short(self, obj):
        return obj.reason[:50] + '...' if len(obj.reason) > 50 else obj.reason
    reason_short.short_description = 'Причина отмены'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('group', 'created_by')

