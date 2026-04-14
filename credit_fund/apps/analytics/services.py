from datetime import timedelta
from decimal import Decimal

from django.db.models import Count, Q, Sum
from django.utils import timezone


class DashboardService:
    """Services for admin dashboard KPIs and charts."""

    @staticmethod
    def get_kpis():
        """Return key performance indicators for the admin dashboard."""
        from apps.guarantees.models import Guarantee

        today = timezone.now().date()
        this_month_start = today.replace(day=1)

        active_qs = Guarantee.objects.filter(state__in=['active', 'issued'])

        return {
            'total_active_guarantees': active_qs.count(),
            'total_exposure': active_qs.aggregate(t=Sum('amount'))['t'] or Decimal('0'),
            'expiring_this_month': active_qs.filter(
                expiry_date__gte=this_month_start,
                expiry_date__lte=today + timedelta(days=30),
            ).count(),
            'pending_approvals': Guarantee.objects.filter(state='under_review').count(),
            'blocked_by_framework': Guarantee.objects.filter(
                framework_status='BLOCKED', state='under_review',
            ).count(),
        }

    @staticmethod
    def get_guarantees_by_type():
        """Guarantees grouped by type (for pie chart)."""
        from apps.guarantees.models import Guarantee

        return list(
            Guarantee.objects.filter(state__in=['active', 'issued'])
            .values('guarantee_type__name_fa')
            .annotate(count=Count('id'))
            .order_by('-count')
        )

    @staticmethod
    def get_monthly_issuance(months=12):
        """Monthly issuance trend (for bar chart)."""
        from apps.guarantees.models import Guarantee

        today = timezone.now().date()
        start = today - timedelta(days=months * 30)

        return list(
            Guarantee.objects.filter(issue_date__gte=start, issue_date__isnull=False)
            .extra(select={'month': "TO_CHAR(issue_date, 'YYYY-MM')"})
            .values('month')
            .annotate(count=Count('id'), total=Sum('amount'))
            .order_by('month')
        )

    @staticmethod
    def get_top_clients_by_exposure(limit=10):
        """Top N clients by total active guarantee exposure."""
        from apps.clients.models import Client

        return list(
            Client.objects.filter(
                guarantees__state__in=['active', 'issued'],
            ).annotate(
                exposure=Sum('guarantees__amount'),
            ).order_by('-exposure')[:limit]
            .values('client_code', 'exposure')
        )

    @staticmethod
    def get_state_distribution():
        """Count of guarantees by state."""
        from apps.guarantees.models import Guarantee

        return list(
            Guarantee.objects.values('state')
            .annotate(count=Count('id'))
            .order_by('state')
        )

    @staticmethod
    def get_framework_stats():
        """Pass/fail/override ratio for credit framework."""
        from apps.creditframework.models import CreditEvaluation

        return list(
            CreditEvaluation.objects.values('status')
            .annotate(count=Count('id'))
            .order_by('status')
        )

    @staticmethod
    def get_recent_transitions(limit=20):
        """Last N state transitions."""
        from apps.guarantees.models import GuaranteeStateTransition

        return list(
            GuaranteeStateTransition.objects.select_related(
                'guarantee', 'transitioned_by',
            ).order_by('-created_at')[:limit]
        )

    @staticmethod
    def get_expiry_calendar(days=30):
        """Guarantees expiring in the next N days."""
        from apps.guarantees.models import Guarantee

        today = timezone.now().date()
        return list(
            Guarantee.objects.filter(
                state__in=['active', 'issued'],
                expiry_date__gte=today,
                expiry_date__lte=today + timedelta(days=days),
            ).select_related('client', 'guarantee_type')
            .order_by('expiry_date')
            .values('guarantee_number', 'client__client_code', 'expiry_date',
                    'guarantee_type__name_fa', 'amount')
        )


class ReportService:
    """Report generation services (Excel/PDF exports)."""

    @staticmethod
    def guarantee_register(filters=None):
        """Full guarantee list with filters — returns queryset for export."""
        from apps.guarantees.models import Guarantee

        qs = Guarantee.objects.select_related(
            'client', 'beneficiary', 'guarantee_type',
        ).order_by('-created_at')

        if filters:
            if filters.get('state'):
                qs = qs.filter(state=filters['state'])
            if filters.get('guarantee_type'):
                qs = qs.filter(guarantee_type_id=filters['guarantee_type'])
            if filters.get('date_from'):
                qs = qs.filter(created_at__date__gte=filters['date_from'])
            if filters.get('date_to'):
                qs = qs.filter(created_at__date__lte=filters['date_to'])

        return qs

    @staticmethod
    def export_to_excel(queryset, fields, filename='report.xlsx'):
        """Export a queryset to Excel bytes using openpyxl."""
        from io import BytesIO

        from openpyxl import Workbook
        from openpyxl.styles import Alignment, Font

        wb = Workbook()
        ws = wb.active
        ws.sheet_view.rightToLeft = True  # RTL for Persian

        # Header row
        for col, field in enumerate(fields, 1):
            cell = ws.cell(row=1, column=col, value=field['label'])
            cell.font = Font(bold=True)
            cell.alignment = Alignment(horizontal='right')

        # Data rows
        for row_idx, obj in enumerate(queryset, 2):
            for col_idx, field in enumerate(fields, 1):
                value = obj
                for attr in field['key'].split('.'):
                    value = getattr(value, attr, '')
                    if callable(value):
                        value = value()
                ws.cell(row=row_idx, column=col_idx, value=str(value) if value else '')

        buffer = BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        return buffer.read()

    @staticmethod
    def client_exposure_report():
        """Per-client exposure summary."""
        from apps.clients.models import Client

        return Client.objects.filter(is_active=True).annotate(
            active_guarantee_count=Count(
                'guarantees', filter=Q(guarantees__state__in=['active', 'issued']),
            ),
            total_exposure=Sum(
                'guarantees__amount', filter=Q(guarantees__state__in=['active', 'issued']),
            ),
        ).filter(total_exposure__gt=0).order_by('-total_exposure')

    @staticmethod
    def fee_collection_report(date_from=None, date_to=None):
        """Outstanding vs collected fees."""
        from apps.guarantees.models import FeeSchedule

        qs = FeeSchedule.objects.all()
        if date_from:
            qs = qs.filter(due_date__gte=date_from)
        if date_to:
            qs = qs.filter(due_date__lte=date_to)

        return {
            'total_fees': qs.aggregate(t=Sum('amount'))['t'] or Decimal('0'),
            'collected': qs.filter(is_paid=True).aggregate(t=Sum('amount'))['t'] or Decimal('0'),
            'outstanding': qs.filter(is_paid=False).aggregate(t=Sum('amount'))['t'] or Decimal('0'),
        }
