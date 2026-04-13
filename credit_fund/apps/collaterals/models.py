from django.db import models

from apps.core.models import UserTrackingModel, TimeStampedModel
from apps.core.validators import validate_file_extension, validate_file_size


def collateral_document_path(instance, filename):
    return f'collaterals/{instance.collateral.id}/{filename}'


class Collateral(UserTrackingModel):
    """Collateral owned by a client, pledgeable against guarantees."""

    class CollateralType(models.TextChoices):
        REAL_ESTATE = 'REAL_ESTATE', 'ملک'
        BANK_DEPOSIT = 'BANK_DEPOSIT', 'سپرده بانکی'
        CHECK = 'CHECK', 'چک'
        PROMISSORY_NOTE = 'PROMISSORY_NOTE', 'سفته'
        STOCK = 'STOCK', 'سهام'
        EQUIPMENT = 'EQUIPMENT', 'تجهیزات'
        OTHER = 'OTHER', 'سایر'

    class Status(models.TextChoices):
        AVAILABLE = 'AVAILABLE', 'آزاد'
        PLEDGED = 'PLEDGED', 'در رهن'
        RELEASED = 'RELEASED', 'آزاد شده'
        SEIZED = 'SEIZED', 'توقیف شده'

    client = models.ForeignKey(
        'clients.Client',
        verbose_name='مشتری',
        on_delete=models.CASCADE,
        related_name='collaterals',
    )
    collateral_type = models.CharField('نوع وثیقه', max_length=20, choices=CollateralType.choices)
    description = models.TextField('توضیحات', blank=True)
    estimated_value = models.DecimalField('ارزش تخمینی (ریال)', max_digits=20, decimal_places=0)
    appraised_value = models.DecimalField(
        'ارزش کارشناسی (ریال)', max_digits=20, decimal_places=0, null=True, blank=True,
    )
    appraisal_date = models.DateField('تاریخ کارشناسی', null=True, blank=True)
    status = models.CharField('وضعیت', max_length=20, choices=Status.choices, default=Status.AVAILABLE)

    class Meta:
        verbose_name = 'وثیقه'
        verbose_name_plural = 'وثایق'

    def __str__(self):
        return f'{self.get_collateral_type_display()} - {self.client}'

    @property
    def effective_value(self):
        return self.appraised_value if self.appraised_value else self.estimated_value

    @property
    def total_pledged(self):
        from decimal import Decimal
        return self.guarantee_collaterals.aggregate(
            total=models.Sum('pledged_amount')
        )['total'] or Decimal('0')

    @property
    def available_value(self):
        return self.effective_value - self.total_pledged


class GuaranteeCollateral(TimeStampedModel):
    """M2M through table: portion of a collateral pledged to a guarantee."""
    guarantee = models.ForeignKey(
        'guarantees.Guarantee',
        verbose_name='ضمانت‌نامه',
        on_delete=models.CASCADE,
        related_name='guarantee_collaterals',
    )
    collateral = models.ForeignKey(
        Collateral,
        verbose_name='وثیقه',
        on_delete=models.CASCADE,
        related_name='guarantee_collaterals',
    )
    pledged_amount = models.DecimalField('مبلغ رهن (ریال)', max_digits=20, decimal_places=0)
    pledged_date = models.DateField('تاریخ رهن', auto_now_add=True)
    released_date = models.DateField('تاریخ آزادسازی', null=True, blank=True)

    class Meta:
        verbose_name = 'وثیقه ضمانت‌نامه'
        verbose_name_plural = 'وثایق ضمانت‌نامه‌ها'
        unique_together = ('guarantee', 'collateral')

    def __str__(self):
        return f'{self.collateral} → {self.guarantee}'


class CollateralDocument(UserTrackingModel):
    """Supporting documents for collaterals."""
    collateral = models.ForeignKey(
        Collateral,
        verbose_name='وثیقه',
        on_delete=models.CASCADE,
        related_name='documents',
    )
    doc_type = models.CharField('نوع مدرک', max_length=100)
    file = models.FileField(
        'فایل',
        upload_to=collateral_document_path,
        validators=[validate_file_size, validate_file_extension],
    )

    class Meta:
        verbose_name = 'مدرک وثیقه'
        verbose_name_plural = 'مدارک وثیقه'

    def __str__(self):
        return f'{self.doc_type} - {self.collateral}'
