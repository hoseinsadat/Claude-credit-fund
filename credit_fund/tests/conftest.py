import pytest

from tests.factories import (
    BeneficiaryFactory,
    ClientFactory,
    CreditTierFactory,
    GuaranteeFactory,
    GuaranteeTypeFactory,
    UserFactory,
)


@pytest.fixture
def analyst_user(db):
    return UserFactory(role='ANALYST')


@pytest.fixture
def accountant_user(db):
    return UserFactory(role='ACCOUNTANT')


@pytest.fixture
def director_user(db):
    return UserFactory(role='DIRECTOR')


@pytest.fixture
def portal_user(db):
    return UserFactory(role='CLIENT_USER', is_portal_user=True)


@pytest.fixture
def client(db, analyst_user):
    return ClientFactory(client_type='LEGAL', created_by=analyst_user)


@pytest.fixture
def guarantee_type(db):
    return GuaranteeTypeFactory()


@pytest.fixture
def beneficiary(db):
    return BeneficiaryFactory()


@pytest.fixture
def guarantee(db, client, guarantee_type, beneficiary, analyst_user):
    return GuaranteeFactory(
        client=client,
        guarantee_type=guarantee_type,
        beneficiary=beneficiary,
        created_by=analyst_user,
    )


@pytest.fixture
def credit_tier(db):
    return CreditTierFactory()
