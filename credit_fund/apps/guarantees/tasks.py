import logging
from datetime import timedelta

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task
def check_expiring_guarantees():
    """Check for guarantees expiring in 30/15/7/1 days and create notifications."""
    from apps.guarantees.models import Guarantee

    today = timezone.now().date()
    alert_days = [30, 15, 7, 1]

    for days in alert_days:
        target_date = today + timedelta(days=days)
        expiring = Guarantee.objects.filter(
            state__in=['active', 'issued'],
            expiry_date=target_date,
        ).select_related('client')

        for guarantee in expiring:
            logger.info(
                'Guarantee %s expiring in %d days (expiry: %s)',
                guarantee.guarantee_number, days, guarantee.expiry_date,
            )
            # Notification will be sent via notification service (Phase 7)


@shared_task
def process_expired_guarantees():
    """Transition past-expiry guarantees to expired state."""
    from apps.guarantees.models import Guarantee
    from apps.guarantees.services import GuaranteeService

    today = timezone.now().date()
    expired_qs = Guarantee.objects.filter(
        state__in=['active', 'issued'],
        expiry_date__lt=today,
    )

    count = 0
    for guarantee in expired_qs:
        if GuaranteeService.process_expiry(guarantee):
            count += 1
            logger.info('Expired guarantee %s', guarantee.guarantee_number)

    logger.info('Processed %d expired guarantees', count)
    return count


@shared_task
def reconcile_client_credits():
    """Nightly reconciliation of all client used_credit values."""
    from apps.clients.models import Client
    from apps.clients.services import ClientService

    clients = Client.objects.filter(is_active=True)
    count = 0
    for client in clients:
        ClientService.update_used_credit(client)
        count += 1

    logger.info('Reconciled credit for %d clients', count)
    return count
