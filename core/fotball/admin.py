from django.contrib import admin
from django.utils.html import format_html
from .models import Child, Trainer, GroupKidGarden, Attendance, User, Parent, TrainingRate


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
    list_display = ('name', 'kindergarten_number', 'age_level', 'trainer')
    list_filter = ('age_level', 'kindergarten_number', 'trainer')
    search_fields = ('name', 'kindergarten_number')
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'kindergarten_number', 'age_level', 'trainer')
        }),
    )


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

