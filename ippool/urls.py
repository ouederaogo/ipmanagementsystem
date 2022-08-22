from django.urls import path
from . import views

urlpatterns = [
    path('', views.ip_address_pool, name='ip_address_pool'),

    path('add-ip-address/',
         views.add_ip_address, name='add_ip_address'),

    path('<slug:slug>/update/',
         views.update_ip_address, name='update_ip_address'),

    path('<slug:slug>/delete/',
         views.delete_ip_address, name='delete_ip_address'),

    path('delete-all-ip-from-pool/',
         views.delete_all_ip_from_pool, name='delete_all_ip_from_pool'),

    path('ip-reports/',
         views.ip_report_list, name='ip_report_list'),
 
    path('generate-ip-report/',
         views.generate_ip_report, name='generate_ip_report'),

    path('send-ip-report/<str:report_id>/',
         views.send_ip_report, name='send_ip_report'),
    
    path('illegal-ip-detected-list/',
         views.illegal_ip_detected_list, name='illegal_ip_detected_list'),
     
     path('ip-addresses-history/',
         views.ip_addresses_history, name='ip_addresses_history'),

]
