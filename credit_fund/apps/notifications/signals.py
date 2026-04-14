import logging

logger = logging.getLogger(__name__)


def on_guarantee_state_change(sender, instance, name, source, target, **kwargs):
    """
    Signal handler connected to django-fsm post_transition.
    Sends notifications based on guarantee state changes.
    """
    from apps.accounts.models import User
    from .services import NotificationService

    guarantee = instance
    context = {
        'guarantee': guarantee,
        'guarantee_number': guarantee.guarantee_number,
        'client_name': guarantee.client.display_name,
        'amount': f'{guarantee.amount:,.0f}',
    }

    if target == 'under_review':
        # Notify Directors
        directors = User.objects.filter(role=User.Role.DIRECTOR, is_active=True)
        for director in directors:
            NotificationService.send_notification(
                director, 'GUARANTEE_SUBMITTED', context, related_object=guarantee,
            )

    elif target == 'approved':
        # Notify Accountants
        accountants = User.objects.filter(role=User.Role.ACCOUNTANT, is_active=True)
        for accountant in accountants:
            NotificationService.send_notification(
                accountant, 'GUARANTEE_APPROVED', context, related_object=guarantee,
            )

    elif target == 'issued':
        # Notify Client portal user
        portal_user = guarantee.client.portal_user
        if portal_user:
            NotificationService.send_notification(
                portal_user, 'GUARANTEE_ISSUED', context, related_object=guarantee,
            )

    elif target == 'expired':
        # Notify Analyst + Client
        analysts = User.objects.filter(role=User.Role.ANALYST, is_active=True)
        for analyst in analysts:
            NotificationService.send_notification(
                analyst, 'GUARANTEE_EXPIRED', context, related_object=guarantee,
            )
        portal_user = guarantee.client.portal_user
        if portal_user:
            NotificationService.send_notification(
                portal_user, 'GUARANTEE_EXPIRED', context, related_object=guarantee,
            )

    # Framework BLOCKED
    if hasattr(instance, 'framework_status') and instance.framework_status == 'BLOCKED':
        directors = User.objects.filter(role=User.Role.DIRECTOR, is_active=True)
        for director in directors:
            NotificationService.send_notification(
                director, 'FRAMEWORK_BLOCKED', context, related_object=guarantee,
            )
