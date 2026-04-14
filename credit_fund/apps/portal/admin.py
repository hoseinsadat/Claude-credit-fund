from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import GuaranteeRequest


@admin.register(GuaranteeRequest)
class GuaranteeRequestAdmin(ModelAdmin):
    list_display = ('client', 'guarantee_type', 'beneficiary_name', 'requested_amount',
                    'status', 'created_at')
    list_filter = ('status', 'guarantee_type')
    search_fields = ('client__client_code', 'beneficiary_name')
    readonly_fields = ('client', 'submitted_by', 'created_at', 'updated_at',
                       'converted_to_guarantee')
    actions = ['convert_to_guarantee']

    fieldsets = (
        ('اطلاعات درخواست', {
            'fields': ('client', 'submitted_by', 'guarantee_type', 'beneficiary_name',
                       'beneficiary_info', 'requested_amount', 'purpose',
                       'requested_duration_months'),
        }),
        ('بررسی', {
            'fields': ('status', 'reviewer_notes', 'converted_to_guarantee'),
        }),
        ('تاریخ‌ها', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    @admin.action(description='تبدیل به ضمانت‌نامه')
    def convert_to_guarantee(self, request, queryset):
        from .services import PortalService
        count = 0
        for req in queryset.filter(status=GuaranteeRequest.Status.SUBMITTED):
            try:
                PortalService.convert_request_to_guarantee(req, by_user=request.user)
                count += 1
            except Exception as e:
                self.message_user(request, f'خطا در تبدیل درخواست {req.pk}: {e}', level='error')
        self.message_user(request, f'{count} درخواست به ضمانت‌نامه تبدیل شد.')
