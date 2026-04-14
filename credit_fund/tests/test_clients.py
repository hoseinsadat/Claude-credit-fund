import pytest
from decimal import Decimal

from apps.clients.models import Client
from apps.clients.services import ClientService
from tests.factories import ClientFactory, LegalPersonProfileFactory, UserFactory


@pytest.mark.django_db
class TestClientModel:
    def test_auto_client_code(self):
        client = ClientFactory()
        assert client.client_code.startswith('CL-')

    def test_available_credit(self):
        client = ClientFactory(credit_limit=Decimal('10000000000'), used_credit=Decimal('3000000000'))
        assert client.available_credit == Decimal('7000000000')

    def test_legal_profile_signal(self):
        """Client creation should auto-create a profile via signal."""
        client = Client.objects.create(
            client_type='LEGAL',
            credit_limit=Decimal('1000000000'),
        )
        assert hasattr(client, 'legal_profile')

    def test_display_name_legal(self):
        profile = LegalPersonProfileFactory(company_name='شرکت تست')
        client = profile.client
        assert 'شرکت تست' in client.display_name


@pytest.mark.django_db
class TestClientService:
    def test_check_credit_availability_sufficient(self):
        client = ClientFactory(credit_limit=Decimal('10000000000'), used_credit=Decimal('0'))
        result = ClientService.check_credit_availability(client, Decimal('5000000000'))
        assert result['available'] is True
        assert result['shortfall'] == Decimal('0')

    def test_check_credit_availability_insufficient(self):
        client = ClientFactory(credit_limit=Decimal('1000000000'), used_credit=Decimal('900000000'))
        result = ClientService.check_credit_availability(client, Decimal('500000000'))
        assert result['available'] is False
        assert result['shortfall'] == Decimal('400000000')
