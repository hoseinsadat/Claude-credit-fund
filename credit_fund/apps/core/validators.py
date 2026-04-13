import re

from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator


def validate_iranian_national_code(value):
    """Validate Iranian national code (کد ملی) — 10-digit check."""
    if not re.match(r'^\d{10}$', value):
        raise ValidationError('کد ملی باید ۱۰ رقم باشد.')

    if len(set(value)) == 1:
        raise ValidationError('کد ملی نامعتبر است.')

    check_sum = sum(int(value[i]) * (10 - i) for i in range(9))
    remainder = check_sum % 11
    control_digit = int(value[9])

    if remainder < 2:
        if control_digit != remainder:
            raise ValidationError('کد ملی نامعتبر است.')
    else:
        if control_digit != 11 - remainder:
            raise ValidationError('کد ملی نامعتبر است.')


def validate_phone_number(value):
    """Validate Iranian mobile phone number (09XXXXXXXXX)."""
    if not re.match(r'^09\d{9}$', value):
        raise ValidationError('شماره تلفن باید با ۰۹ شروع شده و ۱۱ رقم باشد.')


def validate_sheba(value):
    """Validate Iranian SHEBA (IBAN) number — IR followed by 24 digits."""
    if not re.match(r'^IR\d{24}$', value):
        raise ValidationError('شماره شبا باید با IR شروع شده و ۲۶ کاراکتر باشد.')

    # IBAN check digit validation
    rearranged = value[4:] + value[:4]
    numeric_str = ''
    for ch in rearranged:
        if ch.isdigit():
            numeric_str += ch
        else:
            numeric_str += str(ord(ch) - ord('A') + 10)

    if int(numeric_str) % 97 != 1:
        raise ValidationError('شماره شبا نامعتبر است.')


def validate_file_size(value):
    """Validate uploaded file size (max 10 MB)."""
    max_size = 10 * 1024 * 1024  # 10 MB
    if value.size > max_size:
        raise ValidationError(f'حجم فایل نباید بیشتر از ۱۰ مگابایت باشد. حجم فعلی: {value.size / (1024 * 1024):.1f} MB')


# Reusable file extension validator for allowed upload types
validate_file_extension = FileExtensionValidator(
    allowed_extensions=['pdf', 'jpg', 'jpeg', 'png', 'docx'],
    message='فرمت فایل مجاز نیست. فرمت‌های مجاز: pdf, jpg, jpeg, png, docx',
)
