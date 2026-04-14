import logging

from django.contrib.contenttypes.models import ContentType
from django.core.mail import send_mail
from django.template import Context, Template
from django.utils import timezone

from .models import Notification, NotificationTemplate

logger = logging.getLogger(__name__)


class NotificationService:

    @staticmethod
    def send_notification(user, template_code, context=None, channel='IN_APP', related_object=None):
        """Send a notification to a user using a template."""
        if context is None:
            context = {}

        template = NotificationTemplate.objects.filter(code=template_code, is_active=True).first()

        if template:
            title = Template(template.subject_template).render(Context(context))
            body = Template(template.body_template).render(Context(context))
            channel = template.channel
        else:
            title = context.get('title', template_code)
            body = context.get('body', '')

        kwargs = {
            'recipient': user,
            'template': template,
            'title': title,
            'body': body,
            'channel': channel,
        }

        if related_object:
            kwargs['related_content_type'] = ContentType.objects.get_for_model(related_object)
            kwargs['related_object_id'] = related_object.pk

        notification = Notification.objects.create(**kwargs)

        # Dispatch based on channel
        if channel == 'EMAIL':
            NotificationService._send_email(user, title, body)
        elif channel == 'SMS':
            NotificationService._send_sms(user, body)

        return notification

    @staticmethod
    def send_bulk_notification(users, template_code, context=None, related_object=None):
        """Send the same notification to multiple users."""
        notifications = []
        for user in users:
            n = NotificationService.send_notification(
                user, template_code, context, related_object=related_object,
            )
            notifications.append(n)
        return notifications

    @staticmethod
    def mark_as_read(notification_id, user):
        """Mark a notification as read."""
        Notification.objects.filter(
            id=notification_id, recipient=user,
        ).update(is_read=True, read_at=timezone.now())

    @staticmethod
    def _send_email(user, subject, body):
        try:
            send_mail(
                subject=subject,
                message=body,
                from_email=None,  # uses DEFAULT_FROM_EMAIL
                recipient_list=[user.email],
                fail_silently=True,
            )
        except Exception as e:
            logger.error('Failed to send email to %s: %s', user.email, e)

    @staticmethod
    def _send_sms(user, body):
        if not user.phone:
            return
        try:
            from .backends import get_sms_backend
            backend = get_sms_backend()
            backend.send(user.phone, body)
        except Exception as e:
            logger.error('Failed to send SMS to %s: %s', user.phone, e)
