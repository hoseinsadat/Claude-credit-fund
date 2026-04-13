from decimal import Decimal

from django.conf import settings
from django.db import models
from django_fsm import FSMField, transition

from apps.core.models import TimeStampedModel, UserTrackingModel
from apps.core.validators import validate_file_extension, validate_file_size


class GuaranteeType(TimeStampedModel):
    """Predefined guarantee types (seeded via data migration)."""

    code = models.CharField('کد', max_length=30, unique=True)
    name_fa = models.CharField('نام فارسی', max_length=100)
    default_commission_rate = models.DecimalField(
        'نرخ کارمزد پیش‌فرض',
        max_digits=5, decimal_places=4,
        help_text='مثال: 0.0150 = 1.5%',
    )
    default_deposit_ratio = models.DecimalField(
        'نسبت سپرده پیش‌فرض',
        max_digits=5, decimal_places=4,
        default=Decimal('0.1000'),
    )
    typical_duration_months = models.PositiveIntegerField('مدت معمول (ماه)', default=12)
    requires_collateral = models.BooleanField('نیاز به وثیقه', default=True)
    is_active = models.BooleanField('فعال', default=True)

    class Meta:
        verbose_name = 'نوع ضمانت‌نامه'
        verbose_name_plural = 'انواع ضمانت‌نامه'

    def __str__(self):
        return self.name_fa


class Beneficiary(TimeStampedModel):
    """Entity that a guarantee is issued TO on behalf of a client."""

    class BeneficiaryType(models.TextChoices):
        GOVERNMENT = 'GOVERNMENT', 'دولتی'
        PRIVATE = 'PRIVATE', 'خصوصی'
        BANK = 'BANK', 'بانک'
        OTHER = 'OTHER', 'سایر'

    name = models.CharField('نام', max_length=255)
    beneficiary_type = models.CharField(
        'نوع ذینفع',
        max_length=20,
        choices=BeneficiaryType.choices,
    )
    national_id = models.CharField('شناسه ملی / کد ملی', max_length=20, blank=True)
    registration_number = models.CharField('شماره ثبت', max_length=50, blank=True)
    address = models.TextField('آدرس', blank=True)
    phone = models.CharField('تلفن', max_length=20, blank=True)
    contact_person = models.CharField('نام رابط', max_length=100, blank=True)
    is_active = models.BooleanField('فعال', default=True)

    class Meta:
        verbose_name = 'ذینفع'
        verbose_name_plural = 'ذینفعان'

    def __str__(self):
        return self.name


class Guarantee(UserTrackingModel):
    """Core guarantee entity with FSM-driven lifecycle."""

    class State(models.TextChoices):
        DRAFT = 'draft', 'پیش‌نویس'
        UNDER_REVIEW = 'under_review', 'در حال بررسی'
        APPROVED = 'approved', 'تأیید شده'
        ISSUED = 'issued', 'صادر شده'
        ACTIVE = 'active', 'فعال'
        EXPIRED = 'expired', 'منقضی شده'
        CANCELLED = 'cancelled', 'ابطال شده'
        CLAIMED = 'claimed', 'مطالبه شده'

    class FrameworkStatus(models.TextChoices):
        PENDING = 'PENDING', 'در انتظار'
        PASS = 'PASS', 'تأیید'
        BLOCKED = 'BLOCKED', 'مسدود'
        OVERRIDDEN = 'OVERRIDDEN', 'بازنگری مدیر'

    guarantee_number = models.CharField('شماره ضمانت‌نامه', max_length=30, unique=True, editable=False)
    client = models.ForeignKey(
        'clients.Client',
        verbose_name='مشتری',
        on_delete=models.PROTECT,
        related_name='guarantees',
    )
    beneficiary = models.ForeignKey(
        Beneficiary,
        verbose_name='ذینفع',
        on_delete=models.PROTECT,
        related_name='guarantees',
    )
    guarantee_type = models.ForeignKey(
        GuaranteeType,
        verbose_name='نوع ضمانت‌نامه',
        on_delete=models.PROTECT,
        related_name='guarantees',
    )
    state = FSMField('وضعیت', default=State.DRAFT, choices=State.choices, protected=True)
    framework_status = models.CharField(
        'وضعیت چارچوب اعتباری',
        max_length=20,
        choices=FrameworkStatus.choices,
        default=FrameworkStatus.PENDING,
    )
    credit_evaluation = models.ForeignKey(
        'creditframework.CreditEvaluation',
        verbose_name='ارزیابی اعتباری',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='guarantees',
    )
    amount = models.DecimalField('مبلغ (ریال)', max_digits=20, decimal_places=0)
    currency = models.CharField('ارز', max_length=3, default='IRR')
    issue_date = models.DateField('تاریخ صدور', null=True, blank=True)
    effective_date = models.DateField('تاریخ اعتبار', null=True, blank=True)
    expiry_date = models.DateField('تاریخ انقضا', null=True, blank=True)
    purpose = models.TextField('موضوع / شرح', blank=True)

    deposit_amount = models.DecimalField(
        'مبلغ سپرده (ریال)', max_digits=20, decimal_places=0, default=0,
    )
    commission_rate = models.DecimalField(
        'نرخ کارمزد', max_digits=5, decimal_places=4, default=Decimal('0.0000'),
    )
    commission_amount = models.DecimalField(
        'مبلغ کارمزد (ریال)', max_digits=20, decimal_places=0, default=0,
    )

    contract = models.ForeignKey(
        'contracts.Contract',
        verbose_name='قرارداد',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='guarantees',
    )
    parent_guarantee = models.ForeignKey(
        'self',
        verbose_name='ضمانت‌نامه مادر (تمدید)',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='renewals',
    )
    renewal_count = models.PositiveIntegerField('تعداد تمدید', default=0)

    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='بررسی کننده',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='+',
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='تأیید کننده',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='+',
    )
    rejection_reason = models.TextField('دلیل رد / بازگشت', blank=True)

    class Meta:
        verbose_name = 'ضمانت‌نامه'
        verbose_name_plural = 'ضمانت‌نامه‌ها'
        permissions = [
            ('can_submit_guarantee', 'ارسال ضمانت‌نامه برای بررسی'),
            ('can_approve_guarantee', 'تأیید ضمانت‌نامه'),
            ('can_issue_guarantee', 'صدور ضمانت‌نامه'),
            ('can_cancel_guarantee', 'ابطال ضمانت‌نامه'),
        ]
        indexes = [
            models.Index(fields=['client', 'state']),
            models.Index(fields=['expiry_date']),
            models.Index(fields=['state']),
            models.Index(fields=['framework_status']),
        ]

    def __str__(self):
        return f'{self.guarantee_number} - {self.client}'

    def save(self, *args, **kwargs):
        if not self.guarantee_number:
            from apps.core.utils import generate_guarantee_number
            self.guarantee_number = generate_guarantee_number()
        super().save(*args, **kwargs)

    @property
    def fees_paid(self):
        """Check if all required fees are paid."""
        unpaid = self.fee_schedules.filter(is_paid=False).exists()
        return not unpaid

    # ── FSM Transitions ──

    @transition(field=state, source=State.DRAFT, target=State.UNDER_REVIEW,
                permission='guarantees.can_submit_guarantee')
    def submit_for_review(self, by_user=None):
        """Analyst submits guarantee for Director review."""
        self.reviewed_by = None

    @transition(field=state, source=State.UNDER_REVIEW, target=State.APPROVED,
                permission='guarantees.can_approve_guarantee',
                conditions=[lambda g: g.framework_status != 'BLOCKED'])
    def approve(self, by_user=None):
        """Director approves the guarantee."""
        self.approved_by = by_user

    @transition(field=state, source=State.UNDER_REVIEW, target=State.DRAFT,
                permission='guarantees.can_approve_guarantee')
    def return_for_revision(self, by_user=None, reason=''):
        """Director returns the guarantee for revision."""
        self.rejection_reason = reason

    @transition(field=state, source=State.APPROVED, target=State.ISSUED,
                permission='guarantees.can_issue_guarantee',
                conditions=[lambda g: g.fees_paid])
    def issue(self, by_user=None):
        """Accountant issues the guarantee after verifying fees."""
        from django.utils import timezone
        if not self.issue_date:
            self.issue_date = timezone.now().date()

    @transition(field=state, source=State.ISSUED, target=State.ACTIVE)
    def activate(self):
        """Auto-activate after effective_date."""
        pass

    @transition(field=state, source=[State.ACTIVE, State.ISSUED], target=State.EXPIRED)
    def expire(self):
        """Called by Celery beat when guarantee passes expiry_date."""
        pass

    @transition(field=state, source=[State.ACTIVE, State.ISSUED], target=State.CANCELLED,
                permission='guarantees.can_cancel_guarantee')
    def cancel(self, by_user=None, reason=''):
        """Cancel the guarantee."""
        self.rejection_reason = reason

    # CLAIMED transition — stubbed for future use
    # @transition(field=state, source=State.ACTIVE, target=State.CLAIMED)
    # def claim(self, by_user=None):
    #     pass


class GuaranteeStateTransition(TimeStampedModel):
    """Audit log for guarantee state changes (supplement to django-fsm-log)."""
    guarantee = models.ForeignKey(
        Guarantee,
        verbose_name='ضمانت‌نامه',
        on_delete=models.CASCADE,
        related_name='state_transitions',
    )
    source_state = models.CharField('وضعیت مبدأ', max_length=20)
    target_state = models.CharField('وضعیت مقصد', max_length=20)
    transitioned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='توسط',
        on_delete=models.SET_NULL,
        null=True,
        related_name='+',
    )
    comment = models.TextField('توضیحات', blank=True)

    class Meta:
        verbose_name = 'تغییر وضعیت ضمانت‌نامه'
        verbose_name_plural = 'تغییرات وضعیت ضمانت‌نامه'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.guarantee.guarantee_number}: {self.source_state} → {self.target_state}'


class GuaranteeLetter(TimeStampedModel):
    """The actual issued guarantee letter document."""
    guarantee = models.OneToOneField(
        Guarantee,
        verbose_name='ضمانت‌نامه',
        on_delete=models.CASCADE,
        related_name='letter',
    )
    letter_number = models.CharField('شماره نامه', max_length=30, unique=True)
    letter_date = models.DateField('تاریخ نامه')
    template_used = models.CharField('قالب مورد استفاده', max_length=100, blank=True)
    generated_pdf = models.FileField('فایل PDF', upload_to='guarantee_letters/pdf/', blank=True)
    generated_docx = models.FileField('فایل DOCX', upload_to='guarantee_letters/docx/', blank=True)
    is_signed = models.BooleanField('امضا شده', default=False)
    signed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='امضا کننده',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='+',
    )

    class Meta:
        verbose_name = 'نامه ضمانت‌نامه'
        verbose_name_plural = 'نامه‌های ضمانت‌نامه'

    def __str__(self):
        return self.letter_number

    def save(self, *args, **kwargs):
        if not self.letter_number:
            from apps.core.utils import generate_letter_number
            self.letter_number = generate_letter_number()
        super().save(*args, **kwargs)


class FeeSchedule(TimeStampedModel):
    """Fees owed for a guarantee."""

    class FeeType(models.TextChoices):
        COMMISSION = 'COMMISSION', 'کارمزد'
        STAMP_DUTY = 'STAMP_DUTY', 'حق تمبر'
        SERVICE_FEE = 'SERVICE_FEE', 'هزینه خدمات'
        RENEWAL_FEE = 'RENEWAL_FEE', 'هزینه تمدید'

    guarantee = models.ForeignKey(
        Guarantee,
        verbose_name='ضمانت‌نامه',
        on_delete=models.CASCADE,
        related_name='fee_schedules',
    )
    fee_type = models.CharField('نوع هزینه', max_length=20, choices=FeeType.choices)
    amount = models.DecimalField('مبلغ (ریال)', max_digits=20, decimal_places=0)
    calculation_basis = models.TextField('مبنای محاسبه', blank=True)
    due_date = models.DateField('تاریخ سررسید', null=True, blank=True)
    is_paid = models.BooleanField('پرداخت شده', default=False)

    class Meta:
        verbose_name = 'جدول هزینه'
        verbose_name_plural = 'جدول هزینه‌ها'

    def __str__(self):
        return f'{self.guarantee.guarantee_number} - {self.get_fee_type_display()}'


class Payment(TimeStampedModel):
    """Financial transactions for guarantees."""

    class PaymentType(models.TextChoices):
        DEPOSIT = 'DEPOSIT', 'سپرده'
        COMMISSION = 'COMMISSION', 'کارمزد'
        REFUND = 'REFUND', 'بازپرداخت'
        RENEWAL_FEE = 'RENEWAL_FEE', 'هزینه تمدید'

    class PaymentMethod(models.TextChoices):
        BANK_TRANSFER = 'BANK_TRANSFER', 'انتقال بانکی'
        CHECK = 'CHECK', 'چک'
        CASH = 'CASH', 'نقدی'
        ONLINE = 'ONLINE', 'آنلاین'

    client = models.ForeignKey(
        'clients.Client',
        verbose_name='مشتری',
        on_delete=models.PROTECT,
        related_name='payments',
    )
    guarantee = models.ForeignKey(
        Guarantee,
        verbose_name='ضمانت‌نامه',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payments',
    )
    fee_schedule = models.ForeignKey(
        FeeSchedule,
        verbose_name='ردیف هزینه',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payments',
    )
    payment_type = models.CharField('نوع پرداخت', max_length=20, choices=PaymentType.choices)
    amount = models.DecimalField('مبلغ (ریال)', max_digits=20, decimal_places=0)
    payment_method = models.CharField('روش پرداخت', max_length=20, choices=PaymentMethod.choices)
    reference_number = models.CharField('شماره مرجع', max_length=100, blank=True)
    payment_date = models.DateField('تاریخ پرداخت')
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='تأیید کننده',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='+',
    )
    is_verified = models.BooleanField('تأیید شده', default=False)

    class Meta:
        verbose_name = 'پرداخت'
        verbose_name_plural = 'پرداخت‌ها'

    def __str__(self):
        return f'{self.get_payment_type_display()} - {self.amount:,.0f} ریال'
