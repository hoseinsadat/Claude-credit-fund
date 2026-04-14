"""
Seed data for GuaranteeTypes and NotificationTemplates.
Run via: python manage.py shell < apps/guarantees/seed_data.py
Or call seed_all() from a management command.
"""
from decimal import Decimal


def seed_guarantee_types():
    from apps.guarantees.models import GuaranteeType

    types = [
        {'code': 'BID_BOND', 'name_fa': 'ضمانت‌نامه شرکت در مناقصه', 'default_commission_rate': Decimal('0.0100'), 'default_deposit_ratio': Decimal('0.1000'), 'typical_duration_months': 3, 'requires_collateral': False},
        {'code': 'PERFORMANCE_BOND', 'name_fa': 'ضمانت‌نامه حسن انجام کار', 'default_commission_rate': Decimal('0.0150'), 'default_deposit_ratio': Decimal('0.1000'), 'typical_duration_months': 12, 'requires_collateral': True},
        {'code': 'ADVANCE_PAYMENT', 'name_fa': 'ضمانت‌نامه پیش‌پرداخت', 'default_commission_rate': Decimal('0.0150'), 'default_deposit_ratio': Decimal('0.1000'), 'typical_duration_months': 12, 'requires_collateral': True},
        {'code': 'RETENTION', 'name_fa': 'ضمانت‌نامه استرداد کسور', 'default_commission_rate': Decimal('0.0120'), 'default_deposit_ratio': Decimal('0.1000'), 'typical_duration_months': 24, 'requires_collateral': True},
        {'code': 'CUSTOMS', 'name_fa': 'ضمانت‌نامه گمرکی', 'default_commission_rate': Decimal('0.0200'), 'default_deposit_ratio': Decimal('0.1500'), 'typical_duration_months': 6, 'requires_collateral': True},
        {'code': 'GOOD_EXECUTION', 'name_fa': 'ضمانت‌نامه حسن اجرای تعهدات', 'default_commission_rate': Decimal('0.0150'), 'default_deposit_ratio': Decimal('0.1000'), 'typical_duration_months': 12, 'requires_collateral': True},
    ]

    for t in types:
        GuaranteeType.objects.update_or_create(code=t['code'], defaults=t)
    print(f'Seeded {len(types)} guarantee types.')


def seed_notification_templates():
    from apps.notifications.models import NotificationTemplate

    templates = [
        {'code': 'GUARANTEE_SUBMITTED', 'channel': 'IN_APP', 'subject_template': 'ضمانت‌نامه {{ guarantee_number }} ارسال شد', 'body_template': 'ضمانت‌نامه {{ guarantee_number }} مشتری {{ client_name }} به مبلغ {{ amount }} ریال برای بررسی ارسال شده است.'},
        {'code': 'GUARANTEE_APPROVED', 'channel': 'IN_APP', 'subject_template': 'ضمانت‌نامه {{ guarantee_number }} تأیید شد', 'body_template': 'ضمانت‌نامه {{ guarantee_number }} تأیید شد. لطفاً هزینه‌ها را بررسی و صدور کنید.'},
        {'code': 'GUARANTEE_ISSUED', 'channel': 'IN_APP', 'subject_template': 'ضمانت‌نامه {{ guarantee_number }} صادر شد', 'body_template': 'ضمانت‌نامه شماره {{ guarantee_number }} به مبلغ {{ amount }} ریال صادر شد.'},
        {'code': 'GUARANTEE_EXPIRED', 'channel': 'IN_APP', 'subject_template': 'ضمانت‌نامه {{ guarantee_number }} منقضی شد', 'body_template': 'ضمانت‌نامه {{ guarantee_number }} مشتری {{ client_name }} منقضی شده است.'},
        {'code': 'FRAMEWORK_BLOCKED', 'channel': 'IN_APP', 'subject_template': 'ضمانت‌نامه {{ guarantee_number }} مسدود شد', 'body_template': 'ضمانت‌نامه {{ guarantee_number }} توسط چارچوب اعتباری مسدود شده و نیاز به بازنگری مدیر دارد.'},
        {'code': 'GUARANTEE_EXPIRY_30D', 'channel': 'IN_APP', 'subject_template': 'هشدار انقضا: {{ guarantee_number }}', 'body_template': 'ضمانت‌نامه {{ guarantee_number }} در {{ days_remaining }} روز دیگر منقضی می‌شود.'},
        {'code': 'GUARANTEE_EXPIRY_15D', 'channel': 'IN_APP', 'subject_template': 'هشدار انقضا: {{ guarantee_number }}', 'body_template': 'ضمانت‌نامه {{ guarantee_number }} در {{ days_remaining }} روز دیگر منقضی می‌شود.'},
        {'code': 'GUARANTEE_EXPIRY_7D', 'channel': 'IN_APP', 'subject_template': 'هشدار انقضا: {{ guarantee_number }}', 'body_template': 'ضمانت‌نامه {{ guarantee_number }} در {{ days_remaining }} روز دیگر منقضی می‌شود.'},
        {'code': 'GUARANTEE_EXPIRY_1D', 'channel': 'IN_APP', 'subject_template': 'هشدار فوری انقضا: {{ guarantee_number }}', 'body_template': 'ضمانت‌نامه {{ guarantee_number }} فردا منقضی می‌شود!'},
    ]

    for t in templates:
        NotificationTemplate.objects.update_or_create(code=t['code'], defaults=t)
    print(f'Seeded {len(templates)} notification templates.')


def seed_all():
    seed_guarantee_types()
    seed_notification_templates()


if __name__ == '__main__':
    import django
    import os
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
    django.setup()
    seed_all()
