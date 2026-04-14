from django.urls import path

from . import views

app_name = 'portal'

urlpatterns = [
    path('', views.PortalDashboardView.as_view(), name='dashboard'),
    path('guarantees/', views.GuaranteeListView.as_view(), name='guarantee-list'),
    path('guarantees/<int:pk>/', views.GuaranteeDetailView.as_view(), name='guarantee-detail'),
    path('requests/', views.GuaranteeRequestListView.as_view(), name='request-list'),
    path('requests/new/', views.GuaranteeRequestCreateView.as_view(), name='request-create'),
    path('payments/', views.PaymentListView.as_view(), name='payment-list'),
    path('notifications/', views.NotificationListView.as_view(), name='notification-list'),
]
