from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from unfold.admin import ModelAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin):
    list_display = ('username', 'get_full_name', 'role', 'national_code', 'phone', 'is_active', 'is_staff')
    list_filter = ('role', 'is_active', 'is_staff', 'is_portal_user')
    search_fields = ('username', 'first_name', 'last_name', 'national_code', 'phone', 'email')
    ordering = ('-date_joined',)

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('اطلاعات شخصی', {
            'fields': ('first_name', 'last_name', 'email', 'national_code', 'phone'),
        }),
        ('نقش و دسترسی', {
            'fields': ('role', 'is_portal_user', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('تاریخ‌ها', {
            'fields': ('last_login', 'date_joined'),
        }),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'role', 'first_name', 'last_name', 'email', 'national_code', 'phone'),
        }),
    )

    @admin.display(description='نام کامل')
    def get_full_name(self, obj):
        return obj.get_full_name() or '-'
