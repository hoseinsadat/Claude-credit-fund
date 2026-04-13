import random
import string

import jdatetime
from django.utils import timezone


def _jalali_year():
    """Return current Jalali year as a 4-digit string."""
    now = timezone.now()
    return str(jdatetime.datetime.fromgregorian(datetime=now).year)


def generate_client_code():
    """Generate a unique client code like CL-1403-0001."""
    from apps.clients.models import Client

    year = _jalali_year()
    prefix = f'CL-{year}-'
    last = (
        Client.objects.filter(client_code__startswith=prefix)
        .order_by('-client_code')
        .values_list('client_code', flat=True)
        .first()
    )
    if last:
        seq = int(last.split('-')[-1]) + 1
    else:
        seq = 1
    return f'{prefix}{seq:04d}'


def generate_guarantee_number():
    """Generate a unique guarantee number like GR-1403-00001."""
    from apps.guarantees.models import Guarantee

    year = _jalali_year()
    prefix = f'GR-{year}-'
    last = (
        Guarantee.objects.filter(guarantee_number__startswith=prefix)
        .order_by('-guarantee_number')
        .values_list('guarantee_number', flat=True)
        .first()
    )
    if last:
        seq = int(last.split('-')[-1]) + 1
    else:
        seq = 1
    return f'{prefix}{seq:05d}'


def generate_contract_number():
    """Generate a unique contract number like CN-1403-0001."""
    from apps.contracts.models import Contract

    year = _jalali_year()
    prefix = f'CN-{year}-'
    last = (
        Contract.objects.filter(contract_number__startswith=prefix)
        .order_by('-contract_number')
        .values_list('contract_number', flat=True)
        .first()
    )
    if last:
        seq = int(last.split('-')[-1]) + 1
    else:
        seq = 1
    return f'{prefix}{seq:04d}'


def generate_letter_number():
    """Generate a unique guarantee letter number like LT-1403-00001."""
    from apps.guarantees.models import GuaranteeLetter

    year = _jalali_year()
    prefix = f'LT-{year}-'
    last = (
        GuaranteeLetter.objects.filter(letter_number__startswith=prefix)
        .order_by('-letter_number')
        .values_list('letter_number', flat=True)
        .first()
    )
    if last:
        seq = int(last.split('-')[-1]) + 1
    else:
        seq = 1
    return f'{prefix}{seq:05d}'


def generate_random_string(length=8):
    """Generate a random alphanumeric string."""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
