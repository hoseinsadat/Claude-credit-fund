from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models


class NotificationTemplate(models.Model):
    """Reusable notification templates with Jinja2 content."""

    class Channel(models.TextChoices):
        IN_APP = 'IN_APP', 'درون برنامه'
        SMS = 'SMS', 'پیامک'
        EMAIL = 'EMAIL', 'ایمیل'

    code = models.CharField('کد', max_length=50, unique=True)
    channel = models.CharField('کانال', max_length=10, choices=Channel.choices, default=Channel.IN_APP)
    subject_template = models.CharField('قالب عنوان', max_length=255)
    body_template = models.TextField('قالب متن')
    is_active = models.BooleanField('فعال', default=True)

    class Meta:
        verbose_name = 'قالب اعلان'
        verbose_name_plural = 'قالب‌های اعلان'

    def __str__(self):
        return f'{self.code} ({self.get_channel_display()})'


class Notification(models.Model):
    """Individual notification sent to a user."""

    class Channel(models.TextChoices):
        IN_APP = 'IN_APP', 'درون برنامه'
        SMS = 'SMS', 'پیامک'
        EMAIL = 'EMAIL', 'ایمیل'

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='گیرنده',
        on_delete=models.CASCADE,
        related_name='notifications',
    )
    template = models.ForeignKey(
        NotificationTemplate,
        verbose_name='قالب',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    title = models.CharField('عنوان', max_length=255)
    body = models.TextField('متن')
    channel = models.CharField('کانال', max_length=10, choices=Channel.choices, default=Channel.IN_APP)

    # Generic relation to any model
    related_content_type = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    related_object_id = models.PositiveIntegerField(null=True, blank=True)
    related_object = GenericForeignKey('related_content_type', 'related_object_id')

    is_read = models.BooleanField('خوانده شده', default=False)
    read_at = models.DateTimeField('زمان خواندن', null=True, blank=True)
    created_at = models.DateTimeField('تاریخ ایجاد', auto_now_add=True)

    class Meta:
        verbose_name = 'اعلان'
        verbose_name_plural = 'اعلان‌ها'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.title} → {self.recipient}'
