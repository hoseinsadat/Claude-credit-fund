import pytest
from decimal import Decimal

from apps.creditframework.models import CreditEvaluation
from apps.creditframework.services import CreditEvaluationService
from tests.factories import (
    ClientFactory,
    CreditEvaluationFactory,
    CreditTierFactory,
    GuaranteeFactory,
    ScorecardCategoryFactory,
    ScorecardFactorFactory,
    UserFactory,
)


@pytest.mark.django_db
class TestCreditEvaluationService:
    def test_evaluate_client(self):
        client = ClientFactory()
        cat = ScorecardCategoryFactory()
        f1 = ScorecardFactorFactory(category=cat, code='F1', weight=Decimal('50'))
        f2 = ScorecardFactorFactory(category=cat, code='F2', weight=Decimal('50'))
        tier = CreditTierFactory(min_score=Decimal('0'), max_score=Decimal('100'))

        evaluation = CreditEvaluationService.evaluate_client(
            client,
            factor_values={'F1': Decimal('80'), 'F2': Decimal('60')},
        )

        assert evaluation.total_score > 0
        assert evaluation.is_active is True
        assert evaluation.details.count() == 2

    def test_check_guarantee_eligibility_pass(self):
        client = ClientFactory(credit_limit=Decimal('50000000000'))
        CreditEvaluationFactory(
            client=client,
            total_score=Decimal('85'),
            status='PASS',
            is_active=True,
        )
        guarantee = GuaranteeFactory(client=client, amount=Decimal('5000000000'))

        result = CreditEvaluationService.check_guarantee_eligibility(guarantee)
        assert result['eligible'] is True

    def test_check_guarantee_eligibility_exceeds_limit(self):
        tier = CreditTierFactory(max_credit_limit=Decimal('1000000000'))
        client = ClientFactory()
        CreditEvaluationFactory(
            client=client,
            assigned_tier=tier,
            is_active=True,
        )
        guarantee = GuaranteeFactory(client=client, amount=Decimal('2000000000'))

        result = CreditEvaluationService.check_guarantee_eligibility(guarantee)
        assert result['eligible'] is False
        assert len(result['violations']) > 0

    def test_apply_director_override(self):
        client = ClientFactory()
        evaluation = CreditEvaluationFactory(client=client, status='FAIL', is_active=True)
        guarantee = GuaranteeFactory(client=client, framework_status='BLOCKED')
        director = UserFactory(role='DIRECTOR')

        override = CreditEvaluationService.apply_director_override(
            evaluation, guarantee, director, 'دلیل تست', granted_limit=Decimal('10000000000'),
        )

        evaluation.refresh_from_db()
        guarantee.refresh_from_db()
        assert evaluation.status == 'OVERRIDDEN'
        assert guarantee.framework_status == 'OVERRIDDEN'
        assert override.override_reason == 'دلیل تست'
