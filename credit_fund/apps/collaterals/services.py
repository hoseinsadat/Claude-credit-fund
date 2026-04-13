from decimal import Decimal

from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import Collateral, GuaranteeCollateral


class CollateralService:

    @staticmethod
    def pledge(collateral, guarantee, amount):
        """Validate availability, create pledge, update collateral status."""
        available = collateral.available_value
        if amount > available:
            raise ValidationError(
                f'مبلغ درخواستی ({amount:,.0f}) از ارزش آزاد وثیقه ({available:,.0f}) بیشتر است.'
            )

        gc = GuaranteeCollateral.objects.create(
            guarantee=guarantee,
            collateral=collateral,
            pledged_amount=amount,
        )

        # Update collateral status
        if collateral.available_value <= 0:
            collateral.status = Collateral.Status.PLEDGED
        collateral.save(update_fields=['status', 'updated_at'])

        return gc

    @staticmethod
    def release(guarantee_collateral):
        """Release a pledged collateral from a guarantee."""
        guarantee_collateral.released_date = timezone.now().date()
        guarantee_collateral.save(update_fields=['released_date', 'updated_at'])

        collateral = guarantee_collateral.collateral
        # Check if collateral has any remaining unreleased pledges
        active_pledges = collateral.guarantee_collaterals.filter(released_date__isnull=True)
        if not active_pledges.exists():
            collateral.status = Collateral.Status.RELEASED
        elif collateral.available_value > 0:
            collateral.status = Collateral.Status.AVAILABLE
        collateral.save(update_fields=['status', 'updated_at'])

    @staticmethod
    def release_all_for_guarantee(guarantee):
        """Release all collaterals pledged to a guarantee."""
        pledges = GuaranteeCollateral.objects.filter(
            guarantee=guarantee, released_date__isnull=True,
        )
        for pledge in pledges:
            CollateralService.release(pledge)

    @staticmethod
    def get_available_value(collateral):
        """Appraised value minus total pledged."""
        return collateral.available_value
