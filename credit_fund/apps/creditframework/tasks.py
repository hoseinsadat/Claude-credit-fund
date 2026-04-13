import logging

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task
def check_expired_overrides():
    """Find DirectorOverrides past their expiry_date and re-evaluate affected clients."""
    from .models import DirectorOverride
    from .services import CreditEvaluationService

    today = timezone.now().date()
    expired = DirectorOverride.objects.filter(
        expiry_date__lt=today,
        evaluation__is_active=True,
    ).select_related('evaluation__client')

    count = 0
    for override in expired:
        client = override.evaluation.client
        logger.info('Override expired for client %s, re-evaluating', client.client_code)
        # Deactivate the override's evaluation
        override.evaluation.is_active = False
        override.evaluation.save(update_fields=['is_active'])
        count += 1

    logger.info('Processed %d expired overrides', count)
    return count
