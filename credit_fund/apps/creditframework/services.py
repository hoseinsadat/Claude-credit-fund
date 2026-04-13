from decimal import Decimal

from django.db.models import Sum
from django.utils import timezone

from .models import (
    CreditEvaluation,
    CreditEvaluationDetail,
    CreditTier,
    DirectorOverride,
    ScorecardFactor,
)


class CreditEvaluationService:

    @staticmethod
    def evaluate_client(client, guarantee=None, evaluated_by=None, factor_values=None):
        """
        Run all active scorecard factors, calculate weighted scores,
        determine tier, and return a CreditEvaluation.

        factor_values: dict mapping factor.code -> raw_value
        """
        if factor_values is None:
            factor_values = {}

        # Deactivate previous evaluations for this client
        CreditEvaluation.objects.filter(client=client, is_active=True).update(is_active=False)

        evaluation = CreditEvaluation.objects.create(
            client=client,
            guarantee=guarantee,
            evaluated_by=evaluated_by,
            status=CreditEvaluation.Status.PASS,
        )

        active_factors = ScorecardFactor.objects.filter(is_active=True).select_related('category')
        total_weighted = Decimal('0')

        for factor in active_factors:
            raw = factor_values.get(factor.code, Decimal('0'))
            normalized = CreditEvaluationService._normalize_score(factor, raw)
            weighted = normalized * factor.weight / Decimal('100')
            total_weighted += weighted

            CreditEvaluationDetail.objects.create(
                evaluation=evaluation,
                factor=factor,
                raw_value=raw,
                normalized_score=normalized,
                weighted_score=weighted,
            )

        evaluation.total_score = total_weighted

        # Determine tier
        tier = CreditTier.objects.filter(
            is_active=True,
            min_score__lte=total_weighted,
            max_score__gte=total_weighted,
        ).first()

        evaluation.assigned_tier = tier
        if tier:
            evaluation.recommended_credit_limit = tier.max_credit_limit
        else:
            evaluation.recommended_credit_limit = Decimal('0')
            evaluation.status = CreditEvaluation.Status.FAIL

        evaluation.save()
        return evaluation

    @staticmethod
    def _normalize_score(factor, raw_value):
        """Normalize a raw value to 0-100 based on factor's range."""
        if factor.value_type == ScorecardFactor.ValueType.BOOLEAN:
            return Decimal('100') if raw_value else Decimal('0')

        if factor.value_type == ScorecardFactor.ValueType.ENUM:
            # For enum factors, raw_value should already be the score from the option
            option = factor.options.filter(score=raw_value).first()
            return Decimal(str(option.score)) if option else raw_value

        # NUMERIC / PERCENTAGE: linear normalization
        min_v = factor.min_value or Decimal('0')
        max_v = factor.max_value or Decimal('100')
        if max_v == min_v:
            return Decimal('50')

        clamped = max(min_v, min(raw_value, max_v))
        normalized = (clamped - min_v) / (max_v - min_v) * Decimal('100')
        return normalized

    @staticmethod
    def check_guarantee_eligibility(guarantee):
        """
        Evaluate whether this guarantee fits within client's tier limits.
        Returns {eligible, evaluation, violations}.
        """
        client = guarantee.client
        evaluation = CreditEvaluation.objects.filter(
            client=client, is_active=True,
        ).select_related('assigned_tier').first()

        violations = []

        if not evaluation or not evaluation.assigned_tier:
            return {
                'eligible': False,
                'evaluation': evaluation,
                'violations': ['ارزیابی اعتباری فعالی برای مشتری وجود ندارد.'],
            }

        tier = evaluation.assigned_tier

        # Check total exposure
        from apps.guarantees.models import Guarantee
        active_total = Guarantee.objects.filter(
            client=client,
            state__in=['issued', 'active'],
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

        new_total = active_total + guarantee.amount
        if new_total > tier.max_credit_limit:
            violations.append(
                f'مجموع تعهدات ({new_total:,.0f} ریال) از سقف سطح '
                f'{tier.name_fa} ({tier.max_credit_limit:,.0f} ریال) بیشتر است.'
            )

        # Check single guarantee percentage
        max_single = tier.max_credit_limit * tier.max_single_guarantee_pct / Decimal('100')
        if guarantee.amount > max_single:
            violations.append(
                f'مبلغ ضمانت‌نامه ({guarantee.amount:,.0f} ریال) از حداکثر تک ضمانت‌نامه '
                f'({max_single:,.0f} ریال = {tier.max_single_guarantee_pct}%) بیشتر است.'
            )

        eligible = len(violations) == 0
        return {
            'eligible': eligible,
            'evaluation': evaluation,
            'violations': violations,
        }

    @staticmethod
    def apply_director_override(evaluation, guarantee, director_user, reason,
                                 granted_limit=None, expiry_date=None):
        """Create a DirectorOverride, update evaluation status."""
        override = DirectorOverride.objects.create(
            evaluation=evaluation,
            guarantee=guarantee,
            overridden_by=director_user,
            override_reason=reason,
            original_tier=evaluation.assigned_tier,
            granted_credit_limit=granted_limit or evaluation.recommended_credit_limit,
            expiry_date=expiry_date,
        )

        evaluation.status = CreditEvaluation.Status.OVERRIDDEN
        evaluation.save(update_fields=['status', 'updated_at'])

        guarantee.framework_status = 'OVERRIDDEN'
        guarantee.credit_evaluation = evaluation
        guarantee.save(update_fields=['framework_status', 'credit_evaluation', 'updated_at'])

        return override

    @staticmethod
    def get_effective_credit_limit(client):
        """Return the active limit considering latest evaluation + active overrides."""
        evaluation = CreditEvaluation.objects.filter(
            client=client, is_active=True,
        ).select_related('assigned_tier').first()

        if not evaluation:
            return Decimal('0')

        # Check for active overrides
        active_override = DirectorOverride.objects.filter(
            evaluation=evaluation,
        ).exclude(
            expiry_date__lt=timezone.now().date(),
        ).order_by('-override_date').first()

        if active_override:
            return active_override.granted_credit_limit

        if evaluation.assigned_tier:
            return evaluation.assigned_tier.max_credit_limit

        return evaluation.recommended_credit_limit
