from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedModel, UserTrackingModel
from apps.core.validators import (
    validate_file_extension,
    validate_file_size,
    validate_iranian_national_code,
    validate_phone_number,
    validate_sheba,
)


def client_document_path(instance, filename):
    return f'clients/{instance.client.client_code}/{filename}'


class Client(UserTrackingModel):
    """Core client entity — either a legal or real person."""

    class ClientType(models.TextChoices):
        LEGAL = 'LEGAL', 'حقوقی'
        REAL = 'REAL', 'حقیقی'

    client_type = models.CharField(
        'نوع مشتری',
        max_length=10,
        choices=ClientType.choices,
    )
    client_code = models.CharField(
        'کد مشتری',
        max_length=20,
        unique=True,
        editable=False,
    )
    credit_limit = models.DecimalField(
        'سقف اعتبار (ریال)',
        max_digits=20,
        decimal_places=0,
        default=0,
    )
    used_credit = models.DecimalField(
        'اعتبار مصرف شده (ریال)',
        max_digits=20,
        decimal_places=0,
        default=0,
        editable=False,
    )
    is_active = models.BooleanField('فعال', default=True)
    portal_user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        verbose_name='کاربر پرتال',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='client_profile',
    )

    class Meta:
        verbose_name = 'مشتری'
        verbose_name_plural = 'مشتریان'
        indexes = [
            models.Index(fields=['client_type']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        if self.client_type == self.ClientType.LEGAL:
            profile = getattr(self, 'legal_profile', None)
            return f'{self.client_code} - {profile.company_name}' if profile else self.client_code
        else:
            profile = getattr(self, 'real_profile', None)
            return f'{self.client_code} - {profile.first_name} {profile.last_name}' if profile else self.client_code

    @property
    def available_credit(self):
        """credit_limit - used_credit"""
        return self.credit_limit - self.used_credit

    @property
    def display_name(self):
        if self.client_type == self.ClientType.LEGAL:
            profile = getattr(self, 'legal_profile', None)
            return profile.company_name if profile else self.client_code
        else:
            profile = getattr(self, 'real_profile', None)
            return f'{profile.first_name} {profile.last_name}' if profile else self.client_code

    def save(self, *args, **kwargs):
        if not self.client_code:
            from apps.core.utils import generate_client_code
            self.client_code = generate_client_code()
        super().save(*args, **kwargs)


class LegalPersonProfile(TimeStampedModel):
    """Profile for legal (company) clients."""
    client = models.OneToOneField(
        Client,
        verbose_name='مشتری',
        on_delete=models.CASCADE,
        related_name='legal_profile',
    )
    company_name = models.CharField('نام شرکت', max_length=255)
    registration_number = models.CharField('شماره ثبت', max_length=50, blank=True)
    national_id = models.CharField(
        'شناسه ملی',
        max_length=11,
        blank=True,
    )
    economic_code = models.CharField('کد اقتصادی', max_length=20, blank=True)
    registration_date = models.DateField('تاریخ ثبت', null=True, blank=True)
    ceo_name = models.CharField('نام مدیرعامل', max_length=255, blank=True)
    ceo_national_code = models.CharField(
        'کد ملی مدیرعامل',
        max_length=10,
        blank=True,
        validators=[validate_iranian_national_code],
    )

    class Meta:
        verbose_name = 'پروفایل حقوقی'
        verbose_name_plural = 'پروفایل‌های حقوقی'

    def __str__(self):
        return self.company_name


class RealPersonProfile(TimeStampedModel):
    """Profile for real (individual) clients."""

    class Gender(models.TextChoices):
        MALE = 'MALE', 'مرد'
        FEMALE = 'FEMALE', 'زن'

    client = models.OneToOneField(
        Client,
        verbose_name='مشتری',
        on_delete=models.CASCADE,
        related_name='real_profile',
    )
    first_name = models.CharField('نام', max_length=100)
    last_name = models.CharField('نام خانوادگی', max_length=100)
    father_name = models.CharField('نام پدر', max_length=100, blank=True)
    national_code = models.CharField(
        'کد ملی',
        max_length=10,
        validators=[validate_iranian_national_code],
    )
    birth_date = models.DateField('تاریخ تولد', null=True, blank=True)
    gender = models.CharField(
        'جنسیت',
        max_length=10,
        choices=Gender.choices,
        blank=True,
    )
    id_number = models.CharField('شماره شناسنامه', max_length=20, blank=True)

    class Meta:
        verbose_name = 'پروفایل حقیقی'
        verbose_name_plural = 'پروفایل‌های حقیقی'

    def __str__(self):
        return f'{self.first_name} {self.last_name}'


class ClientContact(TimeStampedModel):
    """Multi-type contact information for clients."""

    class ContactType(models.TextChoices):
        PHONE = 'PHONE', 'تلفن'
        EMAIL = 'EMAIL', 'ایمیل'
        FAX = 'FAX', 'فکس'
        ADDRESS = 'ADDRESS', 'آدرس'

    client = models.ForeignKey(
        Client,
        verbose_name='مشتری',
        on_delete=models.CASCADE,
        related_name='contacts',
    )
    contact_type = models.CharField(
        'نوع تماس',
        max_length=10,
        choices=ContactType.choices,
    )
    value = models.TextField('مقدار')
    is_primary = models.BooleanField('اصلی', default=False)

    class Meta:
        verbose_name = 'اطلاعات تماس'
        verbose_name_plural = 'اطلاعات تماس'

    def __str__(self):
        return f'{self.get_contact_type_display()}: {self.value}'


class ClientDocument(UserTrackingModel):
    """Uploaded documents for clients."""

    class DocType(models.TextChoices):
        NATIONAL_CARD = 'NATIONAL_CARD', 'کارت ملی'
        REGISTRATION_CERT = 'REGISTRATION_CERT', 'گواهی ثبت'
        ARTICLES_OF_ASSOCIATION = 'ARTICLES_OF_ASSOCIATION', 'اساسنامه'
        FINANCIAL_STATEMENT = 'FINANCIAL_STATEMENT', 'صورت‌های مالی'
        TAX_CLEARANCE = 'TAX_CLEARANCE', 'مفاصا حساب مالیاتی'
        OFFICIAL_GAZETTE = 'OFFICIAL_GAZETTE', 'روزنامه رسمی'
        POWER_OF_ATTORNEY = 'POWER_OF_ATTORNEY', 'وکالت‌نامه'
        OTHER = 'OTHER', 'سایر'

    client = models.ForeignKey(
        Client,
        verbose_name='مشتری',
        on_delete=models.CASCADE,
        related_name='documents',
    )
    doc_type = models.CharField(
        'نوع مدرک',
        max_length=30,
        choices=DocType.choices,
    )
    file = models.FileField(
        'فایل',
        upload_to=client_document_path,
        validators=[validate_file_size, validate_file_extension],
    )
    description = models.CharField('توضیحات', max_length=255, blank=True)

    class Meta:
        verbose_name = 'مدرک مشتری'
        verbose_name_plural = 'مدارک مشتری'

    def __str__(self):
        return f'{self.client.client_code} - {self.get_doc_type_display()}'


class ClientBankAccount(TimeStampedModel):
    """Bank account information for clients."""
    client = models.ForeignKey(
        Client,
        verbose_name='مشتری',
        on_delete=models.CASCADE,
        related_name='bank_accounts',
    )
    bank_name = models.CharField('نام بانک', max_length=100)
    branch = models.CharField('شعبه', max_length=100, blank=True)
    account_number = models.CharField('شماره حساب', max_length=30)
    sheba = models.CharField(
        'شماره شبا',
        max_length=26,
        blank=True,
        validators=[validate_sheba],
    )
    card_number = models.CharField('شماره کارت', max_length=16, blank=True)
    is_primary = models.BooleanField('حساب اصلی', default=False)

    class Meta:
        verbose_name = 'حساب بانکی'
        verbose_name_plural = 'حساب‌های بانکی'

    def __str__(self):
        return f'{self.bank_name} - {self.account_number}'
