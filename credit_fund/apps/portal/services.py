from apps.guarantees.models import Beneficiary, Guarantee

from .models import GuaranteeRequest


class PortalService:

    @staticmethod
    def convert_request_to_guarantee(guarantee_request, by_user=None):
        """Convert a GuaranteeRequest into a real Guarantee."""
        # Find or create beneficiary
        beneficiary, _ = Beneficiary.objects.get_or_create(
            name=guarantee_request.beneficiary_name,
            defaults={
                'beneficiary_type': Beneficiary.BeneficiaryType.OTHER,
            },
        )

        guarantee = Guarantee(
            client=guarantee_request.client,
            beneficiary=beneficiary,
            guarantee_type=guarantee_request.guarantee_type,
            amount=guarantee_request.requested_amount,
            purpose=guarantee_request.purpose,
            commission_rate=guarantee_request.guarantee_type.default_commission_rate,
            created_by=by_user,
        )
        guarantee.save()

        guarantee_request.status = GuaranteeRequest.Status.CONVERTED
        guarantee_request.converted_to_guarantee = guarantee
        guarantee_request.save(update_fields=['status', 'converted_to_guarantee', 'updated_at'])

        return guarantee
