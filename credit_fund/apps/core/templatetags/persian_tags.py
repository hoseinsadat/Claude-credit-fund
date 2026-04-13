import jdatetime
from django import template

register = template.Library()

PERSIAN_DIGITS = '۰۱۲۳۴۵۶۷۸۹'


@register.filter(name='to_persian')
def to_persian_digits(value):
    """Convert Latin digits to Persian digits."""
    value_str = str(value)
    return ''.join(PERSIAN_DIGITS[int(ch)] if ch.isdigit() else ch for ch in value_str)


@register.filter(name='to_jalali')
def to_jalali(value, fmt='%Y/%m/%d'):
    """Convert a Gregorian datetime/date to Jalali date string."""
    if value is None:
        return ''
    try:
        if hasattr(value, 'hour'):
            jdt = jdatetime.datetime.fromgregorian(datetime=value)
        else:
            jdt = jdatetime.date.fromgregorian(date=value)
        return jdt.strftime(fmt)
    except (ValueError, AttributeError):
        return str(value)


@register.filter(name='to_jalali_full')
def to_jalali_full(value):
    """Convert to Jalali with time: 1403/01/15 14:30"""
    if value is None:
        return ''
    try:
        jdt = jdatetime.datetime.fromgregorian(datetime=value)
        return jdt.strftime('%Y/%m/%d %H:%M')
    except (ValueError, AttributeError):
        return str(value)


@register.filter(name='rials_format')
def rials_format(value):
    """Format a number as Rials with thousand separators in Persian digits."""
    if value is None:
        return ''
    try:
        formatted = '{:,.0f}'.format(value)
        persian = to_persian_digits(formatted)
        return f'{persian} ریال'
    except (ValueError, TypeError):
        return str(value)
