from django.conf import settings
from django.db import models


class TimeStampedModel(models.Model):
    """Abstract base model with created/updated timestamps."""
    created_at = models.DateTimeField('تاریخ ایجاد', auto_now_add=True)
    updated_at = models.DateTimeField('تاریخ بروزرسانی', auto_now=True)

    class Meta:
        abstract = True


class UserTrackingModel(TimeStampedModel):
    """Abstract base model that tracks which user created/updated the record."""
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='ایجاد شده توسط',
        on_delete=models.PROTECT,
        related_name='+',
        null=True,
        blank=True,
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='بروزرسانی شده توسط',
        on_delete=models.PROTECT,
        related_name='+',
        null=True,
        blank=True,
    )

    class Meta:
        abstract = True
