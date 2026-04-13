from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline
from unfold.decorators import action

from apps.core.mixins import UserTrackingAdminMixin

from .models import Contract, ContractDocument, DocumentTemplate


class ContractDocumentInline(TabularInline):
    model = ContractDocument
    extra = 0
    fields = ('doc_type', 'file', 'version')


@admin.register(Contract)
class ContractAdmin(UserTrackingAdminMixin, ModelAdmin):
    list_display = ('contract_number', 'client', 'contract_type', 'total_value',
                    'status', 'start_date', 'end_date')
    list_filter = ('contract_type', 'status')
    search_fields = ('contract_number', 'client__client_code')
    readonly_fields = ('contract_number', 'created_by', 'updated_by', 'created_at', 'updated_at')
    autocomplete_fields = ('client',)
    inlines = [ContractDocumentInline]
    actions_detail = ['action_activate', 'action_complete', 'action_generate_doc']

    fieldsets = (
        ('اطلاعات قرارداد', {
            'fields': ('contract_number', 'client', 'contract_type', 'status'),
        }),
        ('تاریخ و ارزش', {
            'fields': ('start_date', 'end_date', 'total_value', 'signed_date',
                       'signed_by_client', 'signed_by_director'),
        }),
        ('اطلاعات سیستمی', {
            'fields': ('created_by', 'updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    @action(description='فعال‌سازی قرارداد', url_path='activate')
    def action_activate(self, request, object_id):
        contract = self.get_object(request, object_id)
        if contract.status == Contract.Status.DRAFT:
            contract.activate()
            contract.save()
        from django.http import HttpResponseRedirect
        from django.urls import reverse
        return HttpResponseRedirect(reverse('admin:contracts_contract_change', args=[object_id]))

    @action(description='تکمیل قرارداد', url_path='complete')
    def action_complete(self, request, object_id):
        contract = self.get_object(request, object_id)
        if contract.status == Contract.Status.ACTIVE:
            contract.complete()
            contract.save()
        from django.http import HttpResponseRedirect
        from django.urls import reverse
        return HttpResponseRedirect(reverse('admin:contracts_contract_change', args=[object_id]))

    @action(description='تولید سند PDF', url_path='generate-doc')
    def action_generate_doc(self, request, object_id):
        contract = self.get_object(request, object_id)
        from .document_generator import DocumentService
        DocumentService.generate_contract(contract, format='pdf')
        from django.http import HttpResponseRedirect
        from django.urls import reverse
        return HttpResponseRedirect(reverse('admin:contracts_contract_change', args=[object_id]))


@admin.register(DocumentTemplate)
class DocumentTemplateAdmin(ModelAdmin):
    list_display = ('name', 'code', 'template_type', 'format', 'is_active')
    list_filter = ('template_type', 'format', 'is_active')
    search_fields = ('name', 'code')
    fieldsets = (
        ('اطلاعات قالب', {
            'fields': ('name', 'code', 'template_type', 'format', 'is_active'),
        }),
        ('محتوا', {
            'fields': ('template_content', 'file', 'variables_schema'),
        }),
    )
