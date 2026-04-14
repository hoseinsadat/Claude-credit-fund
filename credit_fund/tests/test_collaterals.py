import pytest
from decimal import Decimal

from django.core.exceptions import ValidationError

from apps.collaterals.services import CollateralService
from tests.factories import CollateralFactory, GuaranteeFactory


@pytest.mark.django_db
class TestCollateralService:
    def test_pledge(self):
        collateral = CollateralFactory(
            estimated_value=Decimal('5000000000'),
            appraised_value=Decimal('4000000000'),
        )
        guarantee = GuaranteeFactory(client=collateral.client)

        gc = CollateralService.pledge(collateral, guarantee, Decimal('2000000000'))
        assert gc.pledged_amount == Decimal('2000000000')

    def test_pledge_exceeds_value(self):
        collateral = CollateralFactory(
            estimated_value=Decimal('1000000000'),
            appraised_value=Decimal('1000000000'),
        )
        guarantee = GuaranteeFactory(client=collateral.client)

        with pytest.raises(ValidationError):
            CollateralService.pledge(collateral, guarantee, Decimal('2000000000'))

    def test_release(self):
        collateral = CollateralFactory(
            estimated_value=Decimal('5000000000'),
            appraised_value=Decimal('5000000000'),
        )
        guarantee = GuaranteeFactory(client=collateral.client)
        gc = CollateralService.pledge(collateral, guarantee, Decimal('2000000000'))

        CollateralService.release(gc)
        gc.refresh_from_db()
        assert gc.released_date is not None

    def test_available_value(self):
        collateral = CollateralFactory(
            estimated_value=Decimal('5000000000'),
            appraised_value=Decimal('4000000000'),
        )
        assert collateral.available_value == Decimal('4000000000')

        guarantee = GuaranteeFactory(client=collateral.client)
        CollateralService.pledge(collateral, guarantee, Decimal('1000000000'))
        assert collateral.available_value == Decimal('3000000000')
