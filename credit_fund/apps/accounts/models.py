from django.contrib.auth.models import AbstractUser
from django.db import models

from apps.core.validators import validate_iranian_national_code, validate_phone_number


class User(AbstractUser):
    """Custom user model with role-based access and Iranian-specific fields."""

    class Role(models.TextChoices):
        ANALYST = 'ANALYST', 'کارشناس'
        ACCOUNTANT = 'ACCOUNTANT', 'حسابدار'
        DIRECTOR = 'DIRECTOR', 'مدیر'
        CLIENT_USER = 'CLIENT_USER', 'کاربر پرتال'

    role = models.CharField(
        'نقش',
        max_length=20,
        choices=Role.choices,
        default=Role.ANALYST,
    )
    national_code = models.CharField(
        'کد ملی',
        max_length=10,
        blank=True,
        validators=[validate_iranian_national_code],
    )
    phone = models.CharField(
        'شماره تلفن',
        max_length=11,
        blank=True,
        validators=[validate_phone_number],
    )
    is_portal_user = models.BooleanField(
        'کاربر پرتال',
        default=False,
        help_text='آیا این کاربر به پرتال مشتریان دسترسی دارد؟',
    )

    class Meta:
        verbose_name = 'کاربر'
        verbose_name_plural = 'کاربران'

    def __str__(self):
        return self.get_full_name() or self.username

    @property
    def is_analyst(self):
        return self.role == self.Role.ANALYST

    @property
    def is_accountant(self):
        return self.role == self.Role.ACCOUNTANT

    @property
    def is_director(self):
        return self.role == self.Role.DIRECTOR

    @property
    def is_client_user(self):
        return self.role == self.Role.CLIENT_USER
