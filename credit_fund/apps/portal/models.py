from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedModel


class GuaranteeRequest(TimeStampedModel):
    """Request submitted by a portal user, reviewed by Analyst."""

    class Status(models.TextChoices):
        SUBMITTED = 'SUBMITTED', 'ارسال شده'
        UNDER_REVIEW = 'UNDER_REVIEW', 'در حال بررسی'
        CONVERTED = 'CONVERTED', 'تبدیل شده'
        REJECTED = 'REJECTED', 'رد شده'

    client = models.ForeignKey(
        'clients.Client',
        verbose_name='مشتری',
        on_delete=models.CASCADE,
        related_name='guarantee_requests',
    )
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='ارسال شده توسط',
        on_delete=models.SET_NULL,
        null=True,
        related_name='submitted_requests',
    )
    guarantee_type = models.ForeignKey(
        'guarantees.GuaranteeType',
        verbose_name='نوع ضمانت‌نامه',
        on_delete=models.PROTECT,
    )
    beneficiary_name = models.CharField('نام ذینفع', max_length=255)
    beneficiary_info = models.TextField('اطلاعات ذینفع', blank=True)
    requested_amount = models.DecimalField('مبلغ درخواستی (ریال)', max_digits=20, decimal_places=0)
    purpose = models.TextField('موضوع')
    requested_duration_months = models.PositiveIntegerField('مدت درخواستی (ماه)', default=12)
    status = models.CharField(
        'وضعیت', max_length=20, choices=Status.choices, default=Status.SUBMITTED,
    )
    converted_to_guarantee = models.ForeignKey(
        'guarantees.Guarantee',
        verbose_name='ضمانت‌نامه تبدیل‌شده',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='source_request',
    )
    reviewer_notes = models.TextField('یادداشت بررسی‌کننده', blank=True)

    class Meta:
        verbose_name = 'درخواست ضمانت‌نامه'
        verbose_name_plural = 'درخواست‌های ضمانت‌نامه'
        ordering = ['-created_at']

    def __str__(self):
        return f'درخواست {self.client} - {self.guarantee_type}'
