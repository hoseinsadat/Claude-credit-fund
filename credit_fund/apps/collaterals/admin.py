from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from apps.core.mixins import UserTrackingAdminMixin

from .models import Collateral, CollateralDocument, GuaranteeCollateral


class GuaranteeCollateralInline(TabularInline):
    model = GuaranteeCollateral
    extra = 0
    fields = ('guarantee', 'pledged_amount', 'pledged_date', 'released_date')
    readonly_fields = ('pledged_date',)


class CollateralDocumentInline(TabularInline):
    model = CollateralDocument
    extra = 0
    fields = ('doc_type', 'file')


@admin.register(Collateral)
class CollateralAdmin(UserTrackingAdminMixin, ModelAdmin):
    list_display = ('client', 'collateral_type', 'estimated_value', 'appraised_value',
                    'status', 'available_value_display')
    list_filter = ('collateral_type', 'status')
    search_fields = ('client__client_code', 'description')
    readonly_fields = ('created_by', 'updated_by', 'created_at', 'updated_at',
                       'available_value_display', 'total_pledged_display')
    inlines = [GuaranteeCollateralInline, CollateralDocumentInline]

    fieldsets = (
        ('اطلاعات وثیقه', {
            'fields': ('client', 'collateral_type', 'description', 'status'),
        }),
        ('ارزش‌گذاری', {
            'fields': ('estimated_value', 'appraised_value', 'appraisal_date',
                       'total_pledged_display', 'available_value_display'),
        }),
        ('اطلاعات سیستمی', {
            'fields': ('created_by', 'updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    @admin.display(description='ارزش آزاد')
    def available_value_display(self, obj):
        if obj.pk:
            return f'{obj.available_value:,.0f} ریال'
        return '-'

    @admin.display(description='مجموع رهن')
    def total_pledged_display(self, obj):
        if obj.pk:
            return f'{obj.total_pledged:,.0f} ریال'
        return '-'
