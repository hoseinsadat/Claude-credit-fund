import factory
from decimal import Decimal
from factory.django import DjangoModelFactory

from apps.accounts.models import User
from apps.clients.models import Client, LegalPersonProfile, RealPersonProfile
from apps.collaterals.models import Collateral
from apps.contracts.models import Contract
from apps.creditframework.models import (
    CreditEvaluation,
    CreditTier,
    ScorecardCategory,
    ScorecardFactor,
)
from apps.guarantees.models import (
    Beneficiary,
    FeeSchedule,
    Guarantee,
    GuaranteeType,
    Payment,
)


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f'user_{n}')
    email = factory.LazyAttribute(lambda o: f'{o.username}@example.com')
    first_name = factory.Faker('first_name', locale='fa_IR')
    last_name = factory.Faker('last_name', locale='fa_IR')
    role = 'ANALYST'
    is_active = True
    password = factory.PostGenerationMethodCall('set_password', 'testpass123')


class ClientFactory(DjangoModelFactory):
    class Meta:
        model = Client

    client_type = 'LEGAL'
    credit_limit = Decimal('10000000000')  # 10B Rials
    is_active = True


class LegalPersonProfileFactory(DjangoModelFactory):
    class Meta:
        model = LegalPersonProfile

    client = factory.SubFactory(ClientFactory, client_type='LEGAL')
    company_name = factory.Faker('company', locale='fa_IR')
    registration_number = factory.Sequence(lambda n: f'{100000 + n}')
    national_id = factory.Sequence(lambda n: f'{10000000000 + n}')


class RealPersonProfileFactory(DjangoModelFactory):
    class Meta:
        model = RealPersonProfile

    client = factory.SubFactory(ClientFactory, client_type='REAL')
    first_name = factory.Faker('first_name', locale='fa_IR')
    last_name = factory.Faker('last_name', locale='fa_IR')
    national_code = '0012345678'  # Valid placeholder


class GuaranteeTypeFactory(DjangoModelFactory):
    class Meta:
        model = GuaranteeType

    code = factory.Sequence(lambda n: f'TYPE_{n}')
    name_fa = factory.Sequence(lambda n: f'نوع ضمانت‌نامه {n}')
    default_commission_rate = Decimal('0.0150')
    default_deposit_ratio = Decimal('0.1000')
    typical_duration_months = 12
    is_active = True


class BeneficiaryFactory(DjangoModelFactory):
    class Meta:
        model = Beneficiary

    name = factory.Faker('company', locale='fa_IR')
    beneficiary_type = 'GOVERNMENT'
    is_active = True


class GuaranteeFactory(DjangoModelFactory):
    class Meta:
        model = Guarantee

    client = factory.SubFactory(ClientFactory)
    beneficiary = factory.SubFactory(BeneficiaryFactory)
    guarantee_type = factory.SubFactory(GuaranteeTypeFactory)
    amount = Decimal('1000000000')  # 1B Rials
    commission_rate = Decimal('0.0150')
    deposit_amount = Decimal('100000000')


class FeeScheduleFactory(DjangoModelFactory):
    class Meta:
        model = FeeSchedule

    guarantee = factory.SubFactory(GuaranteeFactory)
    fee_type = 'COMMISSION'
    amount = Decimal('15000000')
    is_paid = False


class PaymentFactory(DjangoModelFactory):
    class Meta:
        model = Payment

    client = factory.SubFactory(ClientFactory)
    guarantee = factory.SubFactory(GuaranteeFactory)
    payment_type = 'COMMISSION'
    amount = Decimal('15000000')
    payment_method = 'BANK_TRANSFER'
    payment_date = factory.Faker('date_this_year')
    is_verified = False


class CollateralFactory(DjangoModelFactory):
    class Meta:
        model = Collateral

    client = factory.SubFactory(ClientFactory)
    collateral_type = 'REAL_ESTATE'
    estimated_value = Decimal('5000000000')
    status = 'AVAILABLE'


class ContractFactory(DjangoModelFactory):
    class Meta:
        model = Contract

    client = factory.SubFactory(ClientFactory)
    contract_type = 'GUARANTEE_ISSUANCE'
    total_value = Decimal('1000000000')


class ScorecardCategoryFactory(DjangoModelFactory):
    class Meta:
        model = ScorecardCategory

    name_fa = factory.Sequence(lambda n: f'دسته {n}')
    ordering = factory.Sequence(lambda n: n)


class ScorecardFactorFactory(DjangoModelFactory):
    class Meta:
        model = ScorecardFactor

    category = factory.SubFactory(ScorecardCategoryFactory)
    name_fa = factory.Sequence(lambda n: f'عامل {n}')
    code = factory.Sequence(lambda n: f'FACTOR_{n}')
    weight = Decimal('20.00')
    value_type = 'NUMERIC'
    min_value = Decimal('0')
    max_value = Decimal('100')
    is_active = True


class CreditTierFactory(DjangoModelFactory):
    class Meta:
        model = CreditTier

    name_fa = 'سطح A'
    min_score = Decimal('80.00')
    max_score = Decimal('100.00')
    max_credit_limit = Decimal('50000000000')  # 50B Rials
    max_single_guarantee_pct = Decimal('40.00')
    is_active = True


class CreditEvaluationFactory(DjangoModelFactory):
    class Meta:
        model = CreditEvaluation

    client = factory.SubFactory(ClientFactory)
    total_score = Decimal('85.00')
    assigned_tier = factory.SubFactory(CreditTierFactory)
    recommended_credit_limit = Decimal('50000000000')
    status = 'PASS'
    is_active = True
