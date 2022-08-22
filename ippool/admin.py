from django.contrib import admin
from .models import IPAddressPool, IPReport, IllegalHostDetection, IllegalIPDetectection

# Register your models here.


#Gallery & News
@admin.register(IPAddressPool)
class IPAddressPoolAdmin(admin.ModelAdmin):
    list_display = ('id', "ip_address", "ip_status", 'slug',)
    # list_editable = ('hidden',)


@admin.register(IPReport)
class IPReportAdmin(admin.ModelAdmin):
    list_display = ('id', "report_id", "report", 'generated_date', 'send_to')


@admin.register(IllegalHostDetection)
class IllegalHostDetectionAdmin(admin.ModelAdmin):
    list_display = ('id', 'mac_address', 'mac_address_vendor', 'reveal_owner', 'detected_time')


@admin.register(IllegalIPDetectection)
class IllegalIPDetectectionAdmin(admin.ModelAdmin):
    list_display = ('id', 'illegal_ip')
