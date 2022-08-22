from django.contrib import admin

from .models import IPRequest, MacAddress

# Register your models here.



@admin.register(IPRequest)
class IPRequestAdmin(admin.ModelAdmin):
    list_display = ('id', "request_id", "stuff_user", 'request_status', 
                    'lease_start', 'lease_end')
   

@admin.register(MacAddress)
class IPRequestAdmin(admin.ModelAdmin):
    list_display = ('id', "ip_request", "mac", "mac_vendor")