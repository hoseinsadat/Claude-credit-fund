from decimal import Decimal

from django.utils import timezone


class GuaranteeService:

    @staticmethod
    def calculate_fees(guarantee):
        """Calculate all fees for a guarantee. Returns dict of fee amounts."""
        duration_months = 12
        if guarantee.expiry_date and guarantee.effective_date:
            delta = guarantee.expiry_date - guarantee.effective_date
            duration_months = max(1, delta.days // 30)

        commission = guarantee.amount * guarantee.commission_rate * Decimal(duration_months) / Decimal(12)
        deposit = guarantee.deposit_amount

        return {
            'COMMISSION': {
                'amount': commission,
                'basis': f'مبلغ {guarantee.amount:,.0f} × نرخ {guarantee.commission_rate} × {duration_months}/12 ماه',
            },
            'DEPOSIT': {
                'amount': deposit,
                'basis': f'سپرده نقدی: {deposit:,.0f} ریال',
            },
        }

    @staticmethod
    def create_fee_schedule(guarantee):
        """Create FeeSchedule records for the guarantee."""
        from .models import FeeSchedule

        fees = GuaranteeService.calculate_fees(guarantee)

        created = []
        for fee_type, data in fees.items():
            if fee_type == 'DEPOSIT':
                continue  # Deposit is tracked separately
            if data['amount'] > 0:
                fee = FeeSchedule.objects.create(
                    guarantee=guarantee,
                    fee_type=fee_type,
                    amount=data['amount'],
                    calculation_basis=data['basis'],
                    due_date=guarantee.issue_date or timezone.now().date(),
                )
                created.append(fee)

        # Update commission_amount on guarantee
        commission_fee = fees.get('COMMISSION', {})
        guarantee.commission_amount = commission_fee.get('amount', Decimal('0'))
        guarantee.save(update_fields=['commission_amount', 'updated_at'])

        return created

    @staticmethod
    def check_issuance_readiness(guarantee):
        """Validate all prerequisites for issuing a guarantee."""
        issues = []

        if not guarantee.effective_date:
            issues.append('تاریخ اعتبار تعیین نشده است.')
        if not guarantee.expiry_date:
            issues.append('تاریخ انقضا تعیین نشده است.')
        if guarantee.amount <= 0:
            issues.append('مبلغ ضمانت‌نامه باید بیشتر از صفر باشد.')
        if not guarantee.fees_paid:
            issues.append('هزینه‌های ضمانت‌نامه پرداخت نشده است.')
        if guarantee.framework_status == 'BLOCKED':
            issues.append('چارچوب اعتباری مسدود است.')

        return {
            'ready': len(issues) == 0,
            'issues': issues,
        }

    @staticmethod
    def renew_guarantee(guarantee, by_user=None):
        """Create a renewal (child guarantee) linked to parent."""
        from .models import Guarantee

        new = Guarantee(
            client=guarantee.client,
            beneficiary=guarantee.beneficiary,
            guarantee_type=guarantee.guarantee_type,
            amount=guarantee.amount,
            currency=guarantee.currency,
            commission_rate=guarantee.commission_rate,
            deposit_amount=guarantee.deposit_amount,
            purpose=guarantee.purpose,
            parent_guarantee=guarantee,
            renewal_count=guarantee.renewal_count + 1,
            created_by=by_user,
        )
        new.save()
        return new

    @staticmethod
    def process_expiry(guarantee):
        """Expire a guarantee and release collaterals."""
        if guarantee.state in ['active', 'issued']:
            guarantee.expire()
            guarantee.save()

            # Update client credit
            from apps.clients.services import ClientService
            ClientService.update_used_credit(guarantee.client)

            return True
        return False
