from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import DashboardSnapshot


@admin.register(DashboardSnapshot)
class DashboardSnapshotAdmin(ModelAdmin):
    list_display = ('report_type', 'generated_at')
    list_filter = ('report_type',)
    readonly_fields = ('report_type', 'data', 'generated_at', 'parameters')

    def has_add_permission(self, request):
        return False
