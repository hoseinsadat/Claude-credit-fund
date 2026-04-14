from decimal import Decimal

from django.db.models import Sum
from django.utils import timezone
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.guarantees.models import FeeSchedule, Guarantee, Payment
from apps.notifications.models import Notification
from apps.portal.models import GuaranteeRequest

from .permissions import IsOwnerOfClient, IsPortalUser
from .serializers import (
    ClientProfileSerializer,
    DashboardSerializer,
    GuaranteeDetailSerializer,
    GuaranteeListSerializer,
    GuaranteeRequestCreateSerializer,
    GuaranteeRequestListSerializer,
    NotificationSerializer,
    PaymentListSerializer,
)


class GuaranteeRequestViewSet(mixins.CreateModelMixin, mixins.ListModelMixin,
                               mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """Create new requests, list own requests."""
    permission_classes = [IsPortalUser]

    def get_serializer_class(self):
        if self.action == 'create':
            return GuaranteeRequestCreateSerializer
        return GuaranteeRequestListSerializer

    def get_queryset(self):
        return GuaranteeRequest.objects.filter(
            client__portal_user=self.request.user,
        ).select_related('guarantee_type')


class GuaranteeViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin,
                        viewsets.GenericViewSet):
    """Read-only access to own guarantees."""
    permission_classes = [IsPortalUser]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return GuaranteeDetailSerializer
        return GuaranteeListSerializer

    def get_queryset(self):
        return Guarantee.objects.filter(
            client__portal_user=self.request.user,
        ).select_related('guarantee_type', 'beneficiary')


class PaymentViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """Read-only payment history."""
    permission_classes = [IsPortalUser]
    serializer_class = PaymentListSerializer

    def get_queryset(self):
        return Payment.objects.filter(
            client__portal_user=self.request.user,
        ).order_by('-payment_date')


class NotificationViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """List and mark-read own notifications."""
    permission_classes = [IsPortalUser]
    serializer_class = NotificationSerializer

    def get_queryset(self):
        return Notification.objects.filter(
            recipient=self.request.user,
        ).order_by('-created_at')

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.read_at = timezone.now()
        notification.save(update_fields=['is_read', 'read_at'])
        return Response({'status': 'ok'})


class ClientProfileView(APIView):
    """Read own client profile."""
    permission_classes = [IsPortalUser]

    def get(self, request):
        client = getattr(request.user, 'client_profile', None)
        if not client:
            return Response({'detail': 'پروفایل مشتری یافت نشد.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = ClientProfileSerializer(client)
        return Response(serializer.data)


class DashboardView(APIView):
    """Aggregated stats for the client portal dashboard."""
    permission_classes = [IsPortalUser]

    def get(self, request):
        client = getattr(request.user, 'client_profile', None)
        if not client:
            return Response({'detail': 'پروفایل مشتری یافت نشد.'}, status=status.HTTP_404_NOT_FOUND)

        active_guarantees = Guarantee.objects.filter(
            client=client, state__in=['active', 'issued'],
        )
        total_exposure = active_guarantees.aggregate(
            total=Sum('amount'),
        )['total'] or Decimal('0')

        pending_requests = GuaranteeRequest.objects.filter(
            client=client, status__in=['SUBMITTED', 'UNDER_REVIEW'],
        ).count()

        pending_fees = FeeSchedule.objects.filter(
            guarantee__client=client, is_paid=False,
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

        data = {
            'active_guarantees_count': active_guarantees.count(),
            'total_exposure': total_exposure,
            'pending_requests': pending_requests,
            'pending_fees': pending_fees,
        }
        serializer = DashboardSerializer(data)
        return Response(serializer.data)
