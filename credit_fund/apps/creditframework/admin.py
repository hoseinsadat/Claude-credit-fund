from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from .models import (
    CreditEvaluation,
    CreditEvaluationDetail,
    CreditTier,
    DirectorOverride,
    ScorecardCategory,
    ScorecardFactor,
    ScorecardFactorOption,
)


class ScorecardFactorInline(TabularInline):
    model = ScorecardFactor
    extra = 0
    fields = ('code', 'name_fa', 'weight', 'value_type', 'min_value', 'max_value', 'is_active')


class ScorecardFactorOptionInline(TabularInline):
    model = ScorecardFactorOption
    extra = 1
    fields = ('label_fa', 'score')


class CreditEvaluationDetailInline(TabularInline):
    model = CreditEvaluationDetail
    extra = 0
    fields = ('factor', 'raw_value', 'normalized_score', 'weighted_score', 'notes')
    readonly_fields = ('factor', 'raw_value', 'normalized_score', 'weighted_score')

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(ScorecardCategory)
class ScorecardCategoryAdmin(ModelAdmin):
    list_display = ('name_fa', 'ordering', 'factor_count')
    ordering = ('ordering',)
    inlines = [ScorecardFactorInline]

    @admin.display(description='تعداد عوامل')
    def factor_count(self, obj):
        return obj.factors.count()


@admin.register(ScorecardFactor)
class ScorecardFactorAdmin(ModelAdmin):
    list_display = ('code', 'name_fa', 'category', 'weight', 'value_type', 'is_active')
    list_filter = ('category', 'value_type', 'is_active')
    search_fields = ('code', 'name_fa')
    inlines = [ScorecardFactorOptionInline]


@admin.register(CreditTier)
class CreditTierAdmin(ModelAdmin):
    list_display = ('name_fa', 'min_score', 'max_score', 'max_credit_limit',
                    'max_single_guarantee_pct', 'is_active')
    list_filter = ('is_active',)
    ordering = ('min_score',)


@admin.register(CreditEvaluation)
class CreditEvaluationAdmin(ModelAdmin):
    list_display = ('client', 'total_score', 'assigned_tier', 'status',
                    'is_active', 'evaluation_date')
    list_filter = ('status', 'is_active')
    search_fields = ('client__client_code',)
    readonly_fields = ('client', 'guarantee', 'evaluated_by', 'evaluation_date',
                       'total_score', 'assigned_tier', 'recommended_credit_limit',
                       'status', 'is_active')
    inlines = [CreditEvaluationDetailInline]

    def has_add_permission(self, request):
        return False


@admin.register(DirectorOverride)
class DirectorOverrideAdmin(ModelAdmin):
    list_display = ('guarantee', 'overridden_by', 'override_reason_short',
                    'granted_credit_limit', 'override_date', 'expiry_date')
    list_filter = ('overridden_by',)
    search_fields = ('guarantee__guarantee_number', 'override_reason')
    readonly_fields = ('evaluation', 'guarantee', 'overridden_by', 'override_reason',
                       'original_tier', 'granted_credit_limit', 'override_date')

    @admin.display(description='دلیل')
    def override_reason_short(self, obj):
        if len(obj.override_reason) > 50:
            return obj.override_reason[:50] + '...'
        return obj.override_reason

    def has_add_permission(self, request):
        return False
