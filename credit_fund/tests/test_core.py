import pytest
from django.core.exceptions import ValidationError

from apps.core.validators import (
    validate_file_size,
    validate_iranian_national_code,
    validate_phone_number,
    validate_sheba,
)


class TestIranianNationalCode:
    def test_valid_code(self):
        validate_iranian_national_code('0499370899')

    def test_invalid_length(self):
        with pytest.raises(ValidationError):
            validate_iranian_national_code('12345')

    def test_all_same_digits(self):
        with pytest.raises(ValidationError):
            validate_iranian_national_code('1111111111')

    def test_invalid_check_digit(self):
        with pytest.raises(ValidationError):
            validate_iranian_national_code('0499370891')


class TestPhoneNumber:
    def test_valid_phone(self):
        validate_phone_number('09123456789')

    def test_invalid_prefix(self):
        with pytest.raises(ValidationError):
            validate_phone_number('08123456789')

    def test_invalid_length(self):
        with pytest.raises(ValidationError):
            validate_phone_number('0912345')


class TestSheba:
    def test_invalid_format(self):
        with pytest.raises(ValidationError):
            validate_sheba('XX123456789012345678901234')

    def test_invalid_short(self):
        with pytest.raises(ValidationError):
            validate_sheba('IR1234')
