"""
Integration tests — full guarantee lifecycle with credit framework.
"""
import pytest
from datetime import date, timedelta
from decimal import Decimal

from apps.clients.services import ClientService
from apps.collaterals.services import CollateralService
from apps.creditframework.services import CreditEvaluationService
from apps.guarantees.services import GuaranteeService
from apps.portal.services import PortalService
from tests.factories import (
    BeneficiaryFactory,
    ClientFactory,
    CollateralFactory,
    CreditTierFactory,
    FeeScheduleFactory,
    GuaranteeFactory,
    GuaranteeTypeFactory,
    ScorecardCategoryFactory,
    ScorecardFactorFactory,
    UserFactory,
)


@pytest.mark.django_db
class TestFullGuaranteeLifecycle:
    """
    Create client → evaluate credit → create guarantee → submit →
    framework check → approve → issue → verify fees → expire.
    """

    def test_full_lifecycle(self):
        # Setup users
        analyst = UserFactory(role='ANALYST')
        director = UserFactory(role='DIRECTOR')
        accountant = UserFactory(role='ACCOUNTANT')

        # Setup credit framework
        cat = ScorecardCategoryFactory()
        factor = ScorecardFactorFactory(category=cat, code='SCORE', weight=Decimal('100'))
        tier = CreditTierFactory(
            min_score=Decimal('0'), max_score=Decimal('100'),
            max_credit_limit=Decimal('50000000000'),
            max_single_guarantee_pct=Decimal('50'),
        )

        # Create client
        client = ClientFactory(credit_limit=Decimal('50000000000'))

        # Evaluate credit
        evaluation = CreditEvaluationService.evaluate_client(
            client, factor_values={'SCORE': Decimal('85')}, evaluated_by=analyst,
        )
        assert evaluation.total_score > 0
        assert evaluation.is_active

        # Create guarantee
        guarantee = GuaranteeFactory(
            client=client,
            amount=Decimal('5000000000'),
            effective_date=date.today(),
            expiry_date=date.today() + timedelta(days=365),
            created_by=analyst,
        )

        # Submit for review
        guarantee.submit_for_review(by_user=analyst)
        guarantee.save()
        assert guarantee.state == 'under_review'

        # Check eligibility
        result = CreditEvaluationService.check_guarantee_eligibility(guarantee)
        if result['eligible']:
            guarantee.framework_status = 'PASS'
        else:
            guarantee.framework_status = 'BLOCKED'
        guarantee.save()
        assert guarantee.framework_status == 'PASS'

        # Director approves
        guarantee.approve(by_user=director)
        guarantee.save()
        assert guarantee.state == 'approved'

        # Create fee schedule
        fees = GuaranteeService.create_fee_schedule(guarantee)

        # Mark fees paid
        for fee in guarantee.fee_schedules.all():
            fee.is_paid = True
            fee.save()

        # Accountant issues
        guarantee.issue(by_user=accountant)
        guarantee.save()
        assert guarantee.state == 'issued'

        # Update client credit
        ClientService.update_used_credit(client)
        client.refresh_from_db()
        assert client.used_credit == Decimal('5000000000')

        # Activate
        guarantee.activate()
        guarantee.save()
        assert guarantee.state == 'active'

        # Expire
        guarantee.expire()
        guarantee.save()
        assert guarantee.state == 'expired'

        # Credit reconciled
        ClientService.update_used_credit(client)
        client.refresh_from_db()
        assert client.used_credit == Decimal('0')


@pytest.mark.django_db
class TestFrameworkBlockAndOverride:
    """
    Create guarantee exceeding tier → submit → BLOCKED →
    Director override → approve.
    """

    def test_block_and_override(self):
        analyst = UserFactory(role='ANALYST')
        director = UserFactory(role='DIRECTOR')

        tier = CreditTierFactory(
            min_score=Decimal('0'), max_score=Decimal('100'),
            max_credit_limit=Decimal('1000000000'),  # 1B limit
            max_single_guarantee_pct=Decimal('50'),
        )
        from apps.creditframework.models import CreditEvaluation
        client = ClientFactory()
        evaluation = CreditEvaluation.objects.create(
            client=client, total_score=Decimal('85'), assigned_tier=tier,
            recommended_credit_limit=Decimal('1000000000'), status='PASS', is_active=True,
        )

        # Create guarantee exceeding limit
        guarantee = GuaranteeFactory(
            client=client, amount=Decimal('2000000000'),  # 2B > 1B limit
        )

        # Check eligibility — should fail
        result = CreditEvaluationService.check_guarantee_eligibility(guarantee)
        assert result['eligible'] is False
        guarantee.framework_status = 'BLOCKED'
        guarantee.save()

        # Submit
        guarantee.submit_for_review()
        guarantee.save()

        # Director override
        override = CreditEvaluationService.apply_director_override(
            evaluation, guarantee, director,
            reason='مشتری با سابقه خوب - استثنا',
            granted_limit=Decimal('3000000000'),
        )
        guarantee.refresh_from_db()
        assert guarantee.framework_status == 'OVERRIDDEN'

        # Now can approve
        guarantee.approve(by_user=director)
        guarantee.save()
        assert guarantee.state == 'approved'


@pytest.mark.django_db
class TestPortalRequestFlow:
    """Client submits request → analyst reviews → converts to guarantee."""

    def test_convert_request(self):
        from apps.portal.models import GuaranteeRequest

        analyst = UserFactory(role='ANALYST')
        portal_user = UserFactory(role='CLIENT_USER', is_portal_user=True)
        client = ClientFactory(portal_user=portal_user)
        gt = GuaranteeTypeFactory()

        request = GuaranteeRequest.objects.create(
            client=client,
            submitted_by=portal_user,
            guarantee_type=gt,
            beneficiary_name='شرکت آزمایشی',
            requested_amount=Decimal('1000000000'),
            purpose='تست',
        )
        assert request.status == 'SUBMITTED'

        # Analyst converts
        guarantee = PortalService.convert_request_to_guarantee(request, by_user=analyst)
        request.refresh_from_db()

        assert request.status == 'CONVERTED'
        assert request.converted_to_guarantee == guarantee
        assert guarantee.client == client
        assert guarantee.amount == Decimal('1000000000')
