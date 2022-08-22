from django.urls import path
from . import views

urlpatterns = [
    path('apply-new-ip-address/', views.apply_new_ip_address,
         name='apply_new_ip_address'),

    path('pending-ip-requests/', views.pending_ip_requests,
         name='pending_ip_requests'),

    path('pending-ip-requests/<str:request_id>/', views.pending_ip_request_detail,
         name='pending_ip_request_detail'),

    path('ip-requests-list/', views.ip_requests_list,
         name='ip_requests_list'),

    path('ip-requests-rejected/', views.request_rejected_list,
         name='request_rejected_list'),

    path('my-ip-lease-records/', views.my_ip_lease_records,
         name='my_ip_lease_records'),

]
