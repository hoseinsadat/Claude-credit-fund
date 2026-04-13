from django.contrib import admin
from django.utils.html import format_html
from unfold.admin import ModelAdmin, TabularInline
from unfold.decorators import action

from apps.core.mixins import UserTrackingAdminMixin

from .models import (
    Beneficiary,
    FeeSchedule,
    Guarantee,
    GuaranteeLetter,
    GuaranteeStateTransition,
    GuaranteeType,
    Payment,
)


# ── Inlines ──

class FeeScheduleInline(TabularInline):
    model = FeeSchedule
    extra = 0
    fields = ('fee_type', 'amount', 'calculation_basis', 'due_date', 'is_paid')
    readonly_fields = ('calculation_basis',)


class PaymentInline(TabularInline):
    model = Payment
    extra = 0
    fields = ('payment_type', 'amount', 'payment_method', 'reference_number', 'payment_date', 'is_verified')
    readonly_fields = ('is_verified',)


class GuaranteeLetterInline(TabularInline):
    model = GuaranteeLetter
    extra = 0
    max_num = 1
    fields = ('letter_number', 'letter_date', 'generated_pdf', 'generated_docx', 'is_signed', 'signed_by')
    readonly_fields = ('letter_number',)


class StateTransitionInline(TabularInline):
    model = GuaranteeStateTransition
    extra = 0
    fields = ('source_state', 'target_state', 'transitioned_by', 'comment', 'created_at')
    readonly_fields = ('source_state', 'target_state', 'transitioned_by', 'comment', 'created_at')

    def has_add_permission(self, request, obj=None):
        return False


# ── Main Admin Classes ──

@admin.register(GuaranteeType)
class GuaranteeTypeAdmin(ModelAdmin):
    list_display = ('code', 'name_fa', 'default_commission_rate', 'default_deposit_ratio',
                    'typical_duration_months', 'requires_collateral', 'is_active')
    list_filter = ('is_active', 'requires_collateral')
    search_fields = ('code', 'name_fa')


@admin.register(Beneficiary)
class BeneficiaryAdmin(ModelAdmin):
    list_display = ('name', 'beneficiary_type', 'national_id', 'phone', 'is_active')
    list_filter = ('beneficiary_type', 'is_active')
    search_fields = ('name', 'national_id', 'registration_number')


@admin.register(Guarantee)
class GuaranteeAdmin(UserTrackingAdminMixin, ModelAdmin):
    list_display = ('guarantee_number', 'client', 'guarantee_type', 'amount_display',
                    'state_badge', 'framework_badge', 'expiry_date')
    list_filter = ('state', 'guarantee_type', 'framework_status')
    search_fields = ('guarantee_number', 'client__client_code',
                     'client__legal_profile__company_name',
                     'client__real_profile__last_name')
    readonly_fields = ('guarantee_number', 'state', 'framework_status', 'created_by', 'updated_by',
                       'created_at', 'updated_at', 'reviewed_by', 'approved_by')
    autocomplete_fields = ('client', 'beneficiary')
    ordering = ('-created_at',)
    inlines = [FeeScheduleInline, PaymentInline, GuaranteeLetterInline, StateTransitionInline]

    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('guarantee_number', 'client', 'beneficiary', 'guarantee_type',
                       'state', 'framework_status'),
        }),
        ('مبالغ', {
            'fields': ('amount', 'currency', 'deposit_amount', 'commission_rate', 'commission_amount'),
        }),
        ('تاریخ‌ها', {
            'fields': ('issue_date', 'effective_date', 'expiry_date'),
        }),
        ('جزئیات', {
            'fields': ('purpose', 'contract', 'parent_guarantee', 'renewal_count'),
        }),
        ('بررسی و تأیید', {
            'fields': ('reviewed_by', 'approved_by', 'rejection_reason', 'credit_evaluation'),
        }),
        ('اطلاعات سیستمی', {
            'fields': ('created_by', 'updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    actions_detail = ['action_submit', 'action_approve', 'action_return',
                      'action_issue', 'action_activate', 'action_cancel']

    @admin.display(description='مبلغ')
    def amount_display(self, obj):
        return f'{obj.amount:,.0f} ریال'

    @admin.display(description='وضعیت')
    def state_badge(self, obj):
        colors = {
            'draft': '#6b7280',
            'under_review': '#f59e0b',
            'approved': '#3b82f6',
            'issued': '#8b5cf6',
            'active': '#10b981',
            'expired': '#ef4444',
            'cancelled': '#6b7280',
            'claimed': '#dc2626',
        }
        color = colors.get(obj.state, '#6b7280')
        return format_html(
            '<span style="background:{}; color:white; padding:2px 8px; border-radius:4px; font-size:12px">{}</span>',
            color, obj.get_state_display()
        )

    @admin.display(description='چارچوب اعتباری')
    def framework_badge(self, obj):
        colors = {
            'PENDING': '#6b7280',
            'PASS': '#10b981',
            'BLOCKED': '#ef4444',
            'OVERRIDDEN': '#f59e0b',
        }
        color = colors.get(obj.framework_status, '#6b7280')
        return format_html(
            '<span style="background:{}; color:white; padding:2px 8px; border-radius:4px; font-size:12px">{}</span>',
            color, obj.get_framework_status_display()
        )

    @action(description='ارسال برای بررسی', url_path='submit-for-review')
    def action_submit(self, request, object_id):
        guarantee = self.get_object(request, object_id)
        if guarantee.state == Guarantee.State.DRAFT:
            guarantee.submit_for_review(by_user=request.user)
            guarantee.save()
            self._log_transition(guarantee, 'draft', 'under_review', request.user)
        return self._redirect_to_change(object_id)

    @action(description='تأیید', url_path='approve')
    def action_approve(self, request, object_id):
        guarantee = self.get_object(request, object_id)
        if guarantee.state == Guarantee.State.UNDER_REVIEW and guarantee.framework_status != 'BLOCKED':
            guarantee.approve(by_user=request.user)
            guarantee.save()
            self._log_transition(guarantee, 'under_review', 'approved', request.user)
        return self._redirect_to_change(object_id)

    @action(description='بازگشت برای اصلاح', url_path='return-for-revision')
    def action_return(self, request, object_id):
        guarantee = self.get_object(request, object_id)
        if guarantee.state == Guarantee.State.UNDER_REVIEW:
            guarantee.return_for_revision(by_user=request.user, reason='نیاز به اصلاح')
            guarantee.save()
            self._log_transition(guarantee, 'under_review', 'draft', request.user)
        return self._redirect_to_change(object_id)

    @action(description='صدور', url_path='issue')
    def action_issue(self, request, object_id):
        guarantee = self.get_object(request, object_id)
        if guarantee.state == Guarantee.State.APPROVED and guarantee.fees_paid:
            guarantee.issue(by_user=request.user)
            guarantee.save()
            self._log_transition(guarantee, 'approved', 'issued', request.user)
            # Update client used_credit
            from apps.clients.services import ClientService
            ClientService.update_used_credit(guarantee.client)
        return self._redirect_to_change(object_id)

    @action(description='فعال‌سازی', url_path='activate')
    def action_activate(self, request, object_id):
        guarantee = self.get_object(request, object_id)
        if guarantee.state == Guarantee.State.ISSUED:
            guarantee.activate()
            guarantee.save()
            self._log_transition(guarantee, 'issued', 'active', request.user)
        return self._redirect_to_change(object_id)

    @action(description='ابطال', url_path='cancel')
    def action_cancel(self, request, object_id):
        guarantee = self.get_object(request, object_id)
        if guarantee.state in [Guarantee.State.ACTIVE, Guarantee.State.ISSUED]:
            guarantee.cancel(by_user=request.user, reason='ابطال شده')
            guarantee.save()
            self._log_transition(guarantee, str(guarantee.state), 'cancelled', request.user)
            from apps.clients.services import ClientService
            ClientService.update_used_credit(guarantee.client)
        return self._redirect_to_change(object_id)

    def _log_transition(self, guarantee, source, target, user):
        GuaranteeStateTransition.objects.create(
            guarantee=guarantee,
            source_state=source,
            target_state=target,
            transitioned_by=user,
        )

    def _redirect_to_change(self, object_id):
        from django.http import HttpResponseRedirect
        from django.urls import reverse
        return HttpResponseRedirect(
            reverse('admin:guarantees_guarantee_change', args=[object_id])
        )


@admin.register(FeeSchedule)
class FeeScheduleAdmin(ModelAdmin):
    list_display = ('guarantee', 'fee_type', 'amount', 'due_date', 'is_paid')
    list_filter = ('fee_type', 'is_paid')
    search_fields = ('guarantee__guarantee_number',)


@admin.register(Payment)
class PaymentAdmin(ModelAdmin):
    list_display = ('client', 'guarantee', 'payment_type', 'amount', 'payment_method',
                    'payment_date', 'is_verified')
    list_filter = ('payment_type', 'payment_method', 'is_verified')
    search_fields = ('client__client_code', 'guarantee__guarantee_number', 'reference_number')
    actions = ['verify_payments']

    @admin.action(description='تأیید پرداخت‌های انتخاب شده')
    def verify_payments(self, request, queryset):
        updated = queryset.filter(is_verified=False).update(is_verified=True, verified_by=request.user)
        self.message_user(request, f'{updated} پرداخت تأیید شد.')
        # Mark associated fee_schedules as paid
        for payment in queryset.filter(fee_schedule__isnull=False):
            if payment.fee_schedule:
                payment.fee_schedule.is_paid = True
                payment.fee_schedule.save(update_fields=['is_paid'])


@admin.register(GuaranteeLetter)
class GuaranteeLetterAdmin(ModelAdmin):
    list_display = ('letter_number', 'guarantee', 'letter_date', 'is_signed')
    search_fields = ('letter_number', 'guarantee__guarantee_number')
    readonly_fields = ('letter_number',)
