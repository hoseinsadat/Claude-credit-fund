from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import Notification, NotificationTemplate


@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(ModelAdmin):
    list_display = ('code', 'channel', 'subject_template', 'is_active')
    list_filter = ('channel', 'is_active')
    search_fields = ('code', 'subject_template')


@admin.register(Notification)
class NotificationAdmin(ModelAdmin):
    list_display = ('title', 'recipient', 'channel', 'is_read', 'created_at')
    list_filter = ('channel', 'is_read')
    search_fields = ('title', 'recipient__username')
    readonly_fields = ('recipient', 'template', 'title', 'body', 'channel',
                       'related_content_type', 'related_object_id',
                       'is_read', 'read_at', 'created_at')

    def has_add_permission(self, request):
        return False
