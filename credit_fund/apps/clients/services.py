from decimal import Decimal

from django.db.models import Sum


class ClientService:

    @staticmethod
    def update_used_credit(client):
        """Recalculate used_credit from active guarantees."""
        from apps.guarantees.models import Guarantee

        active_states = ['issued', 'active']
        total = Guarantee.objects.filter(
            client=client,
            state__in=active_states,
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

        client.used_credit = total
        client.save(update_fields=['used_credit', 'updated_at'])

    @staticmethod
    def check_credit_availability(client, amount):
        """Check if the client has enough credit for a new guarantee."""
        available = client.available_credit
        return {
            'available': available >= amount,
            'remaining': available,
            'requested': amount,
            'shortfall': max(Decimal('0'), amount - available),
        }
