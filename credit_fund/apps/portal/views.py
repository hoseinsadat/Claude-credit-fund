from decimal import Decimal

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import CreateView, DetailView, ListView, TemplateView

from apps.guarantees.models import FeeSchedule, Guarantee, Payment
from apps.notifications.models import Notification

from .models import GuaranteeRequest


class PortalMixin(LoginRequiredMixin):
    """Ensure user is a portal user and get their client."""
    login_url = '/accounts/login/'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and not request.user.is_portal_user:
            from django.http import HttpResponseForbidden
            return HttpResponseForbidden('دسترسی به پرتال محدود است.')
        return super().dispatch(request, *args, **kwargs)

    def get_client(self):
        return getattr(self.request.user, 'client_profile', None)


class PortalDashboardView(PortalMixin, TemplateView):
    template_name = 'portal/dashboard.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        client = self.get_client()
        if client:
            active = Guarantee.objects.filter(client=client, state__in=['active', 'issued'])
            ctx['active_guarantees_count'] = active.count()
            ctx['total_exposure'] = active.aggregate(t=Sum('amount'))['t'] or Decimal('0')
            ctx['pending_requests'] = GuaranteeRequest.objects.filter(
                client=client, status__in=['SUBMITTED', 'UNDER_REVIEW'],
            ).count()
            ctx['pending_fees'] = FeeSchedule.objects.filter(
                guarantee__client=client, is_paid=False,
            ).aggregate(t=Sum('amount'))['t'] or Decimal('0')
            ctx['client'] = client
        return ctx


class GuaranteeListView(PortalMixin, ListView):
    template_name = 'portal/guarantee_list.html'
    context_object_name = 'guarantees'
    paginate_by = 20

    def get_queryset(self):
        client = self.get_client()
        if not client:
            return Guarantee.objects.none()
        return Guarantee.objects.filter(
            client=client,
        ).select_related('guarantee_type', 'beneficiary').order_by('-created_at')


class GuaranteeDetailView(PortalMixin, DetailView):
    template_name = 'portal/guarantee_detail.html'
    context_object_name = 'guarantee'

    def get_queryset(self):
        client = self.get_client()
        if not client:
            return Guarantee.objects.none()
        return Guarantee.objects.filter(client=client).select_related(
            'guarantee_type', 'beneficiary',
        ).prefetch_related('fee_schedules', 'payments')


class GuaranteeRequestCreateView(PortalMixin, CreateView):
    model = GuaranteeRequest
    template_name = 'portal/request_create.html'
    fields = ['guarantee_type', 'beneficiary_name', 'beneficiary_info',
              'requested_amount', 'purpose', 'requested_duration_months']

    def form_valid(self, form):
        form.instance.client = self.get_client()
        form.instance.submitted_by = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return '/portal/requests/'


class GuaranteeRequestListView(PortalMixin, ListView):
    template_name = 'portal/request_list.html'
    context_object_name = 'requests'
    paginate_by = 20

    def get_queryset(self):
        client = self.get_client()
        if not client:
            return GuaranteeRequest.objects.none()
        return GuaranteeRequest.objects.filter(
            client=client,
        ).select_related('guarantee_type').order_by('-created_at')


class PaymentListView(PortalMixin, ListView):
    template_name = 'portal/payment_list.html'
    context_object_name = 'payments'
    paginate_by = 20

    def get_queryset(self):
        client = self.get_client()
        if not client:
            return Payment.objects.none()
        return Payment.objects.filter(client=client).order_by('-payment_date')


class NotificationListView(PortalMixin, ListView):
    template_name = 'portal/notification_list.html'
    context_object_name = 'notifications'
    paginate_by = 20

    def get_queryset(self):
        return Notification.objects.filter(
            recipient=self.request.user,
        ).order_by('-created_at')
