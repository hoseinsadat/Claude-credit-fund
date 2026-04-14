import logging

logger = logging.getLogger(__name__)


class BaseSMSBackend:
    """Abstract SMS backend."""

    def send(self, phone, message):
        raise NotImplementedError


class LoggingSMSBackend(BaseSMSBackend):
    """Development SMS backend that logs messages instead of sending."""

    def send(self, phone, message):
        logger.info('SMS to %s: %s', phone, message)
        return True


class KavenegarSMSBackend(BaseSMSBackend):
    """Kavenegar SMS provider backend (placeholder for production)."""

    def __init__(self):
        import os
        self.api_key = os.environ.get('KAVENEGAR_API_KEY', '')

    def send(self, phone, message):
        if not self.api_key:
            logger.error('KAVENEGAR_API_KEY not configured')
            return False
        # Placeholder — integrate kavenegar SDK here
        logger.info('Kavenegar SMS to %s: %s', phone, message)
        return True


def get_sms_backend():
    """Load SMS backend from settings."""
    from django.conf import settings
    from django.utils.module_loading import import_string
    backend_path = getattr(settings, 'SMS_BACKEND', 'apps.notifications.backends.LoggingSMSBackend')
    return import_string(backend_path)()
