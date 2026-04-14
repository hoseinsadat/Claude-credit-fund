import pytest
from datetime import date, timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django_fsm import TransitionNotAllowed

from apps.guarantees.models import Guarantee
from apps.guarantees.services import GuaranteeService
from tests.factories import (
    BeneficiaryFactory,
    ClientFactory,
    FeeScheduleFactory,
    GuaranteeFactory,
    GuaranteeTypeFactory,
    UserFactory,
)


@pytest.mark.django_db
class TestGuaranteeModel:
    def test_auto_guarantee_number(self):
        g = GuaranteeFactory()
        assert g.guarantee_number.startswith('GR-')

    def test_initial_state_is_draft(self):
        g = GuaranteeFactory()
        assert g.state == 'draft'

    def test_fees_paid_no_fees(self):
        """With no fee schedules, fees_paid returns True."""
        g = GuaranteeFactory()
        assert g.fees_paid is True

    def test_fees_paid_unpaid(self):
        g = GuaranteeFactory()
        FeeScheduleFactory(guarantee=g, is_paid=False)
        assert g.fees_paid is False

    def test_fees_paid_all_paid(self):
        g = GuaranteeFactory()
        FeeScheduleFactory(guarantee=g, is_paid=True)
        assert g.fees_paid is True


@pytest.mark.django_db
class TestGuaranteeFSM:
    def test_submit_for_review(self):
        g = GuaranteeFactory()
        g.submit_for_review(by_user=None)
        g.save()
        assert g.state == 'under_review'

    def test_approve_from_under_review(self):
        g = GuaranteeFactory()
        g.submit_for_review()
        g.framework_status = 'PASS'
        g.save()
        director = UserFactory(role='DIRECTOR')
        g.approve(by_user=director)
        g.save()
        assert g.state == 'approved'
        assert g.approved_by == director

    def test_cannot_approve_when_blocked(self):
        g = GuaranteeFactory()
        g.submit_for_review()
        g.framework_status = 'BLOCKED'
        g.save()
        with pytest.raises(TransitionNotAllowed):
            g.approve(by_user=None)

    def test_return_for_revision(self):
        g = GuaranteeFactory()
        g.submit_for_review()
        g.save()
        g.return_for_revision(reason='نیاز به اصلاح')
        g.save()
        assert g.state == 'draft'
        assert g.rejection_reason == 'نیاز به اصلاح'

    def test_issue_requires_fees_paid(self):
        g = GuaranteeFactory()
        g.submit_for_review()
        g.framework_status = 'PASS'
        g.save()
        g.approve(by_user=None)
        g.save()
        FeeScheduleFactory(guarantee=g, is_paid=False)
        with pytest.raises(TransitionNotAllowed):
            g.issue(by_user=None)

    def test_full_lifecycle(self):
        """Test full guarantee lifecycle: draft → under_review → approved → issued → active → expired."""
        g = GuaranteeFactory()
        g.submit_for_review()
        g.framework_status = 'PASS'
        g.save()

        g.approve(by_user=UserFactory(role='DIRECTOR'))
        g.save()
        assert g.state == 'approved'

        # Mark fees paid
        fee = FeeScheduleFactory(guarantee=g, is_paid=True)
        g.issue(by_user=UserFactory(role='ACCOUNTANT'))
        g.save()
        assert g.state == 'issued'

        g.activate()
        g.save()
        assert g.state == 'active'

        g.expire()
        g.save()
        assert g.state == 'expired'


@pytest.mark.django_db
class TestGuaranteeService:
    def test_calculate_fees(self):
        g = GuaranteeFactory(
            amount=Decimal('1000000000'),
            commission_rate=Decimal('0.0150'),
            deposit_amount=Decimal('100000000'),
            effective_date=date.today(),
            expiry_date=date.today() + timedelta(days=365),
        )
        fees = GuaranteeService.calculate_fees(g)
        assert 'COMMISSION' in fees
        assert fees['COMMISSION']['amount'] > 0

    def test_renew_guarantee(self):
        g = GuaranteeFactory()
        user = UserFactory()
        new_g = GuaranteeService.renew_guarantee(g, by_user=user)
        assert new_g.parent_guarantee == g
        assert new_g.renewal_count == g.renewal_count + 1
        assert new_g.client == g.client

    def test_check_issuance_readiness_incomplete(self):
        g = GuaranteeFactory(effective_date=None, expiry_date=None)
        result = GuaranteeService.check_issuance_readiness(g)
        assert result['ready'] is False
        assert len(result['issues']) >= 2
