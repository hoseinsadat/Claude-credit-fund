from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from apps.core.mixins import UserTrackingAdminMixin

from .models import (
    Client,
    ClientBankAccount,
    ClientContact,
    ClientDocument,
    LegalPersonProfile,
    RealPersonProfile,
)


class LegalPersonProfileInline(TabularInline):
    model = LegalPersonProfile
    extra = 0
    max_num = 1
    fields = ('company_name', 'registration_number', 'national_id', 'economic_code',
              'registration_date', 'ceo_name', 'ceo_national_code')


class RealPersonProfileInline(TabularInline):
    model = RealPersonProfile
    extra = 0
    max_num = 1
    fields = ('first_name', 'last_name', 'father_name', 'national_code',
              'birth_date', 'gender', 'id_number')


class ClientContactInline(TabularInline):
    model = ClientContact
    extra = 1
    fields = ('contact_type', 'value', 'is_primary')


class ClientDocumentInline(TabularInline):
    model = ClientDocument
    extra = 0
    fields = ('doc_type', 'file', 'description')
    readonly_fields = ('created_by',)


class ClientBankAccountInline(TabularInline):
    model = ClientBankAccount
    extra = 0
    fields = ('bank_name', 'branch', 'account_number', 'sheba', 'card_number', 'is_primary')


@admin.register(Client)
class ClientAdmin(UserTrackingAdminMixin, ModelAdmin):
    list_display = ('client_code', 'display_name', 'client_type', 'credit_limit',
                    'used_credit', 'available_credit_display', 'is_active')
    list_filter = ('client_type', 'is_active')
    search_fields = ('client_code', 'legal_profile__company_name', 'legal_profile__national_id',
                     'real_profile__first_name', 'real_profile__last_name', 'real_profile__national_code')
    readonly_fields = ('client_code', 'used_credit', 'available_credit_display', 'created_by', 'updated_by',
                       'created_at', 'updated_at')
    ordering = ('-created_at',)

    fieldsets = (
        ('اطلاعات پایه', {
            'fields': ('client_type', 'client_code', 'is_active', 'portal_user'),
        }),
        ('اطلاعات اعتباری', {
            'fields': ('credit_limit', 'used_credit', 'available_credit_display'),
        }),
        ('اطلاعات سیستمی', {
            'fields': ('created_by', 'updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    def get_inlines(self, request, obj=None):
        inlines = []
        if obj is None:
            inlines = [LegalPersonProfileInline, RealPersonProfileInline]
        elif obj.client_type == Client.ClientType.LEGAL:
            inlines = [LegalPersonProfileInline]
        else:
            inlines = [RealPersonProfileInline]
        inlines.extend([ClientContactInline, ClientBankAccountInline, ClientDocumentInline])
        return inlines

    @admin.display(description='اعتبار موجود')
    def available_credit_display(self, obj):
        if obj.pk:
            return f'{obj.available_credit:,.0f} ریال'
        return '-'


@admin.register(ClientDocument)
class ClientDocumentAdmin(UserTrackingAdminMixin, ModelAdmin):
    list_display = ('client', 'doc_type', 'description', 'created_at')
    list_filter = ('doc_type',)
    search_fields = ('client__client_code', 'description')
    readonly_fields = ('created_by', 'updated_by')
