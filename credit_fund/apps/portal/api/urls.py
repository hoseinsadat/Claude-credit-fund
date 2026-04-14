from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    ClientProfileView,
    DashboardView,
    GuaranteeRequestViewSet,
    GuaranteeViewSet,
    NotificationViewSet,
    PaymentViewSet,
)

app_name = 'api'

router = DefaultRouter()
router.register('requests', GuaranteeRequestViewSet, basename='guarantee-request')
router.register('guarantees', GuaranteeViewSet, basename='guarantee')
router.register('payments', PaymentViewSet, basename='payment')
router.register('notifications', NotificationViewSet, basename='notification')

urlpatterns = [
    path('', include(router.urls)),
    path('profile/', ClientProfileView.as_view(), name='client-profile'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
]
