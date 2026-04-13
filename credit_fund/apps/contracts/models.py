from django.conf import settings
from django.db import models
from django_fsm import FSMField, transition

from apps.core.models import TimeStampedModel, UserTrackingModel
from apps.core.validators import validate_file_extension, validate_file_size


class Contract(UserTrackingModel):
    """Contract entity linked to client and guarantees."""

    class ContractType(models.TextChoices):
        GUARANTEE_ISSUANCE = 'GUARANTEE_ISSUANCE', 'صدور ضمانت‌نامه'
        FRAMEWORK = 'FRAMEWORK', 'قرارداد چارچوب'
        AMENDMENT = 'AMENDMENT', 'اصلاحیه'

    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'پیش‌نویس'
        ACTIVE = 'ACTIVE', 'فعال'
        COMPLETED = 'COMPLETED', 'تکمیل شده'
        TERMINATED = 'TERMINATED', 'فسخ شده'

    contract_number = models.CharField('شماره قرارداد', max_length=30, unique=True, editable=False)
    client = models.ForeignKey(
        'clients.Client',
        verbose_name='مشتری',
        on_delete=models.PROTECT,
        related_name='contracts',
    )
    contract_type = models.CharField('نوع قرارداد', max_length=30, choices=ContractType.choices)
    start_date = models.DateField('تاریخ شروع', null=True, blank=True)
    end_date = models.DateField('تاریخ پایان', null=True, blank=True)
    total_value = models.DecimalField('ارزش کل (ریال)', max_digits=20, decimal_places=0, default=0)
    status = FSMField('وضعیت', default=Status.DRAFT, choices=Status.choices)
    signed_date = models.DateField('تاریخ امضا', null=True, blank=True)
    signed_by_client = models.BooleanField('امضای مشتری', default=False)
    signed_by_director = models.BooleanField('امضای مدیر', default=False)

    class Meta:
        verbose_name = 'قرارداد'
        verbose_name_plural = 'قراردادها'

    def __str__(self):
        return f'{self.contract_number} - {self.client}'

    def save(self, *args, **kwargs):
        if not self.contract_number:
            from apps.core.utils import generate_contract_number
            self.contract_number = generate_contract_number()
        super().save(*args, **kwargs)

    @transition(field=status, source=Status.DRAFT, target=Status.ACTIVE)
    def activate(self):
        pass

    @transition(field=status, source=Status.ACTIVE, target=Status.COMPLETED)
    def complete(self):
        pass

    @transition(field=status, source=[Status.DRAFT, Status.ACTIVE], target=Status.TERMINATED)
    def terminate(self):
        pass


class ContractDocument(TimeStampedModel):
    """Versioned document attachments for contracts."""

    class DocType(models.TextChoices):
        ORIGINAL = 'ORIGINAL', 'نسخه اصلی'
        AMENDMENT = 'AMENDMENT', 'اصلاحیه'
        APPENDIX = 'APPENDIX', 'پیوست'

    contract = models.ForeignKey(
        Contract,
        verbose_name='قرارداد',
        on_delete=models.CASCADE,
        related_name='documents',
    )
    doc_type = models.CharField('نوع سند', max_length=20, choices=DocType.choices)
    file = models.FileField(
        'فایل',
        upload_to='contracts/documents/',
        validators=[validate_file_size, validate_file_extension],
    )
    version = models.PositiveIntegerField('نسخه', default=1)

    class Meta:
        verbose_name = 'سند قرارداد'
        verbose_name_plural = 'اسناد قرارداد'

    def __str__(self):
        return f'{self.contract.contract_number} - {self.get_doc_type_display()} v{self.version}'


class DocumentTemplate(TimeStampedModel):
    """Templates for generating guarantee letters, contracts, receipts."""

    class TemplateType(models.TextChoices):
        GUARANTEE_LETTER = 'GUARANTEE_LETTER', 'نامه ضمانت‌نامه'
        CONTRACT = 'CONTRACT', 'قرارداد'
        RECEIPT = 'RECEIPT', 'رسید'
        FEE_STATEMENT = 'FEE_STATEMENT', 'صورتحساب'
        OTHER = 'OTHER', 'سایر'

    class Format(models.TextChoices):
        HTML = 'HTML', 'HTML (برای PDF)'
        DOCX = 'DOCX', 'DOCX (قالب Word)'

    name = models.CharField('نام قالب', max_length=100)
    code = models.CharField('کد', max_length=50, unique=True)
    template_type = models.CharField('نوع قالب', max_length=30, choices=TemplateType.choices)
    format = models.CharField('فرمت', max_length=10, choices=Format.choices)
    file = models.FileField('فایل قالب (DOCX)', upload_to='templates/', blank=True)
    template_content = models.TextField('محتوای قالب (HTML)', blank=True)
    variables_schema = models.JSONField(
        'متغیرهای قالب',
        default=dict,
        blank=True,
        help_text='JSON شامل متغیرهای مورد انتظار قالب',
    )
    is_active = models.BooleanField('فعال', default=True)

    class Meta:
        verbose_name = 'قالب سند'
        verbose_name_plural = 'قالب‌های اسناد'

    def __str__(self):
        return f'{self.name} ({self.get_format_display()})'
