from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedModel


class ScorecardCategory(TimeStampedModel):
    """Grouping of scoring factors (e.g. Financial Ratios, Collateral Quality)."""
    name_fa = models.CharField('نام دسته', max_length=100)
    description = models.TextField('توضیحات', blank=True)
    ordering = models.PositiveIntegerField('ترتیب نمایش', default=0)

    class Meta:
        verbose_name = 'دسته امتیازدهی'
        verbose_name_plural = 'دسته‌های امتیازدهی'
        ordering = ['ordering']

    def __str__(self):
        return self.name_fa


class ScorecardFactor(TimeStampedModel):
    """Individual scoring criterion within a category."""

    class ValueType(models.TextChoices):
        NUMERIC = 'NUMERIC', 'عددی'
        PERCENTAGE = 'PERCENTAGE', 'درصدی'
        ENUM = 'ENUM', 'انتخابی'
        BOOLEAN = 'BOOLEAN', 'بله / خیر'

    category = models.ForeignKey(
        ScorecardCategory,
        verbose_name='دسته',
        on_delete=models.CASCADE,
        related_name='factors',
    )
    name_fa = models.CharField('نام عامل', max_length=150)
    code = models.CharField('کد', max_length=50, unique=True)
    weight = models.DecimalField(
        'وزن',
        max_digits=5, decimal_places=2,
        help_text='مجموع وزن‌ها باید ۱۰۰ باشد',
    )
    value_type = models.CharField(
        'نوع مقدار',
        max_length=20,
        choices=ValueType.choices,
    )
    min_value = models.DecimalField('حداقل مقدار', max_digits=20, decimal_places=4, null=True, blank=True)
    max_value = models.DecimalField('حداکثر مقدار', max_digits=20, decimal_places=4, null=True, blank=True)
    is_active = models.BooleanField('فعال', default=True)

    class Meta:
        verbose_name = 'عامل امتیازدهی'
        verbose_name_plural = 'عوامل امتیازدهی'

    def __str__(self):
        return f'{self.name_fa} (وزن: {self.weight})'


class ScorecardFactorOption(TimeStampedModel):
    """Options for ENUM-type factors (e.g. Collateral Type: Real Estate=100)."""
    factor = models.ForeignKey(
        ScorecardFactor,
        verbose_name='عامل',
        on_delete=models.CASCADE,
        related_name='options',
    )
    label_fa = models.CharField('عنوان', max_length=100)
    score = models.DecimalField('امتیاز', max_digits=5, decimal_places=2)

    class Meta:
        verbose_name = 'گزینه عامل'
        verbose_name_plural = 'گزینه‌های عامل'

    def __str__(self):
        return f'{self.label_fa} = {self.score}'


class CreditTier(TimeStampedModel):
    """Score-to-limit mapping tiers."""
    name_fa = models.CharField('نام سطح', max_length=100)
    min_score = models.DecimalField('حداقل امتیاز', max_digits=5, decimal_places=2)
    max_score = models.DecimalField('حداکثر امتیاز', max_digits=5, decimal_places=2)
    max_credit_limit = models.DecimalField('سقف اعتبار (ریال)', max_digits=20, decimal_places=0)
    max_single_guarantee_pct = models.DecimalField(
        'حداکثر درصد تک ضمانت‌نامه',
        max_digits=5, decimal_places=2,
        default=40,
        help_text='حداکثر درصد از سقف اعتبار برای یک ضمانت‌نامه',
    )
    description = models.TextField('توضیحات', blank=True)
    is_active = models.BooleanField('فعال', default=True)

    class Meta:
        verbose_name = 'سطح اعتباری'
        verbose_name_plural = 'سطوح اعتباری'
        ordering = ['min_score']

    def __str__(self):
        return f'{self.name_fa} ({self.min_score}-{self.max_score})'


class CreditEvaluation(TimeStampedModel):
    """Snapshot of a client's credit evaluation at a point in time."""

    class Status(models.TextChoices):
        PASS = 'PASS', 'تأیید'
        FAIL = 'FAIL', 'رد'
        OVERRIDDEN = 'OVERRIDDEN', 'بازنگری مدیر'

    client = models.ForeignKey(
        'clients.Client',
        verbose_name='مشتری',
        on_delete=models.CASCADE,
        related_name='credit_evaluations',
    )
    guarantee = models.ForeignKey(
        'guarantees.Guarantee',
        verbose_name='ضمانت‌نامه',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='credit_evaluations_direct',
    )
    evaluated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='ارزیاب',
        on_delete=models.SET_NULL,
        null=True,
        related_name='+',
    )
    evaluation_date = models.DateTimeField('تاریخ ارزیابی', auto_now_add=True)
    total_score = models.DecimalField('امتیاز کل', max_digits=5, decimal_places=2, default=0)
    assigned_tier = models.ForeignKey(
        CreditTier,
        verbose_name='سطح اختصاص‌یافته',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='evaluations',
    )
    recommended_credit_limit = models.DecimalField(
        'سقف اعتبار پیشنهادی (ریال)',
        max_digits=20, decimal_places=0, default=0,
    )
    status = models.CharField('وضعیت', max_length=20, choices=Status.choices, default=Status.PASS)
    is_active = models.BooleanField('ارزیابی فعال', default=True,
                                     help_text='آخرین ارزیابی فعال برای هر مشتری')

    class Meta:
        verbose_name = 'ارزیابی اعتباری'
        verbose_name_plural = 'ارزیابی‌های اعتباری'
        ordering = ['-evaluation_date']

    def __str__(self):
        return f'ارزیابی {self.client} - امتیاز: {self.total_score}'


class CreditEvaluationDetail(TimeStampedModel):
    """Per-factor scores for an evaluation."""
    evaluation = models.ForeignKey(
        CreditEvaluation,
        verbose_name='ارزیابی',
        on_delete=models.CASCADE,
        related_name='details',
    )
    factor = models.ForeignKey(
        ScorecardFactor,
        verbose_name='عامل',
        on_delete=models.CASCADE,
        related_name='+',
    )
    raw_value = models.DecimalField('مقدار خام', max_digits=20, decimal_places=4, default=0)
    normalized_score = models.DecimalField('امتیاز نرمال (0-100)', max_digits=5, decimal_places=2, default=0)
    weighted_score = models.DecimalField('امتیاز وزنی', max_digits=7, decimal_places=4, default=0)
    notes = models.TextField('یادداشت', blank=True)

    class Meta:
        verbose_name = 'جزئیات ارزیابی'
        verbose_name_plural = 'جزئیات ارزیابی‌ها'

    def __str__(self):
        return f'{self.factor.name_fa}: {self.weighted_score}'


class DirectorOverride(TimeStampedModel):
    """Record of Director overriding a FAIL evaluation."""
    evaluation = models.ForeignKey(
        CreditEvaluation,
        verbose_name='ارزیابی',
        on_delete=models.CASCADE,
        related_name='overrides',
    )
    guarantee = models.ForeignKey(
        'guarantees.Guarantee',
        verbose_name='ضمانت‌نامه',
        on_delete=models.CASCADE,
        related_name='overrides',
    )
    overridden_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='بازنگری توسط',
        on_delete=models.PROTECT,
        related_name='+',
    )
    override_reason = models.TextField('دلیل بازنگری')
    original_tier = models.ForeignKey(
        CreditTier,
        verbose_name='سطح اصلی',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='+',
    )
    granted_credit_limit = models.DecimalField(
        'سقف اعتبار اعطایی (ریال)',
        max_digits=20, decimal_places=0,
    )
    override_date = models.DateTimeField('تاریخ بازنگری', auto_now_add=True)
    expiry_date = models.DateField('تاریخ انقضا', null=True, blank=True,
                                    help_text='خالی = بدون محدودیت زمانی')

    class Meta:
        verbose_name = 'بازنگری مدیر'
        verbose_name_plural = 'بازنگری‌های مدیر'
        ordering = ['-override_date']

    def __str__(self):
        return f'بازنگری {self.guarantee} توسط {self.overridden_by}'
