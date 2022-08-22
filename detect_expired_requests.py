from time import sleep
import os
import django
from background_tasks_utils.utils import PingDiagnostic, ResolveMac ,get_mac,  get_mac_vendor
from django.template.loader import get_template
from concurrent.futures.thread import ThreadPoolExecutor
import threading
from django.core.mail import EmailMessage
import datetime
os.environ.setdefault('DJANGO_SETTINGS_MODULE',
                      'ipMgntSystemSettings.settings')
django.setup()

logo = """
------------------------------------------------------------------------------------------------------
  ___ ____    _______  ______ ___ ____      _  _____ ___ ___  _   _   ____   ____ ____  ___ ____ _____ 
 |_ _|  _ \  | ____\ \/ /  _ \_ _|  _ \    / \|_   _|_ _/ _ \| \ | | / ___| / ___|  _ \|_ _|  _ \_   _|
  | || |_) | |  _|  \  /| |_) | || |_) |  / _ \ | |  | | | | |  \| | \___ \| |   | |_) || || |_) || |  
  | ||  __/  | |___ /  \|  __/| ||  _ <  / ___ \| |  | | |_| | |\  |  ___) | |___|  _ < | ||  __/ | |  
 |___|_|     |_____/_/\_\_|  |___|_| \_\/_/   \_\_| |___\___/|_| \_| |____/ \____|_| \_\___|_|    |_|  
========================================================================================================                                                             
"""

ACCEPTED = 'accepted'
EXPIRED = 'expired'
UNASSIGNED = 'unassigned'
ASSIGNED = 'assigned'


def detect_expired_requests():
    """
    DETECT Assigned IP mac address and also verify the expiration date for assigned IP
    """
    # run twice a day
    from iprequest.models import IPRequest, MacAddress
    from ippool.models import IPAddressPool
    import ipMgntSystemSettings.settings as my_settings
    
    from accounts.views import _greeting

    valid_ip_requests = IPRequest.objects.filter(request_status=ACCEPTED)
    for ip_request in valid_ip_requests:

        # Resolve mac from IP address to reveal the eligal IP utilization in the future
        ip_objs = [ResolveMac(ip_obj.ip_address) for ip_obj in list(ip_request.assigned_ip.all())]
        pool_ping = ThreadPoolExecutor(max_workers=10)
        for ip_obj in ip_objs:
            pool_ping.submit(ip_obj.get_mac)
        pool_ping.shutdown(wait=True)
        mac_list = [ip_obj.mac for ip_obj in ip_objs if ip_obj.mac]
        for mac in mac_list:
            
            try:
                new_mac_address = MacAddress.objects.get(mac=mac)
            except MacAddress.DoesNotExist:
                print(f"[+] New MAC <<{mac}>> belong to {ip_request.stuff_user} added to the detabase!")
                new_mac_address = MacAddress()
                new_mac_address.mac = mac
                new_mac_address.mac_vendor = get_mac_vendor(mac)
                new_mac_address.ip_request = ip_request
                new_mac_address.save()
            else:
                #don't need to re-create
                pass

        # TODO: Try to check the assigned IP lease_end date and change request_status to 'expired'
        today_date = datetime.datetime.today().date()
        if ip_request.lease_end < today_date and not ip_request.notify:
            print(f"[+] Expired ip request  #{ip_request.request_id} detected, belong to {ip_request.stuff_user}!")

            # send expiration notification
            mail_subject = f'Request# {ip_request.request_id} lease time expired  😭'

            message = get_template(
                'emails/ip_allocate_release_notice_email.html').render({
                    'ip_request': ip_request,
                    'greeting': _greeting(),
                })
            recipents = my_settings.MANAGER_EMAIL.append(ip_request.stuff_user.email)
            send_email = EmailMessage(to=recipents,
                                      subject=mail_subject, body=message)

            send_email.content_subtype = 'html'
            send_email.send(fail_silently=False)
            print(f"[+] IP release Notification sent to  {ip_request.stuff_user} for  request #{ip_request.request_id}!")

            # Update the ip request status
            ip_request.request_status = EXPIRED
            ip_request.notify = True
            ip_request.save()
            # Update the ippool status
            for ip_address in ip_request.assigned_ip.all():
                ip_address.ip_status = UNASSIGNED
                ip_address.save()
                print(f"[+] IP's {ip_address.ip_address} is successfully released!")


if __name__ == '__main__':
    print(logo)
    print("Running now...")
    while True:
        print(f"[{datetime.datetime.today()}]-Started new verification " )
        detect_expired_requests()
        print(f"[{datetime.datetime.today()}]-Ended verification\n\n\nRunning..." )
        sleep(30)
