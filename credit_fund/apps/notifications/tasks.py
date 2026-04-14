import logging
from datetime import timedelta

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task
def send_email_notification(notification_id):
    """Async email dispatch for a notification."""
    from .models import Notification
    from .services import NotificationService

    try:
        notification = Notification.objects.select_related('recipient').get(id=notification_id)
        NotificationService._send_email(notification.recipient, notification.title, notification.body)
    except Notification.DoesNotExist:
        logger.error('Notification %s not found', notification_id)


@shared_task
def send_sms_notification(notification_id):
    """Async SMS dispatch for a notification."""
    from .models import Notification
    from .services import NotificationService

    try:
        notification = Notification.objects.select_related('recipient').get(id=notification_id)
        NotificationService._send_sms(notification.recipient, notification.body)
    except Notification.DoesNotExist:
        logger.error('Notification %s not found', notification_id)


@shared_task
def check_and_send_expiry_notifications():
    """Scheduled daily: send expiry warnings for guarantees expiring in 30/15/7/1 days."""
    from apps.accounts.models import User
    from apps.guarantees.models import Guarantee
    from .services import NotificationService

    today = timezone.now().date()
    alert_days = [30, 15, 7, 1]

    for days in alert_days:
        target_date = today + timedelta(days=days)
        expiring = Guarantee.objects.filter(
            state__in=['active', 'issued'],
            expiry_date=target_date,
        ).select_related('client')

        for guarantee in expiring:
            context = {
                'guarantee_number': guarantee.guarantee_number,
                'client_name': guarantee.client.display_name,
                'expiry_date': str(guarantee.expiry_date),
                'days_remaining': days,
            }

            # Notify analysts
            analysts = User.objects.filter(role=User.Role.ANALYST, is_active=True)
            for analyst in analysts:
                NotificationService.send_notification(
                    analyst, f'GUARANTEE_EXPIRY_{days}D', context, related_object=guarantee,
                )

            # Notify client portal user
            portal_user = guarantee.client.portal_user
            if portal_user:
                NotificationService.send_notification(
                    portal_user, f'GUARANTEE_EXPIRY_{days}D', context, related_object=guarantee,
                )

    logger.info('Expiry notifications check complete')


@shared_task
def send_approval_notification(guarantee_id):
    """Triggered on state transitions — sends appropriate notification."""
    from apps.guarantees.models import Guarantee

    try:
        guarantee = Guarantee.objects.select_related('client').get(id=guarantee_id)
        logger.info('Approval notification for guarantee %s', guarantee.guarantee_number)
    except Guarantee.DoesNotExist:
        logger.error('Guarantee %s not found', guarantee_id)
