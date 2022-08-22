import os
from time import sleep
import django
from background_tasks_utils.utils import PingDiagnostic, ResolveMac, get_mac,  get_mac_vendor
from django.utils import timezone
import time
import datetime
from django.template.loader import get_template
from django.core.mail import EmailMessage
from concurrent.futures.thread import ThreadPoolExecutor
os.environ.setdefault('DJANGO_SETTINGS_MODULE',
                      'ipMgntSystemSettings.settings')
django.setup()


UNASSIGNED = 'unassigned'


# TODO: Detect illegal ip utilization
def detect_illegal_ip_utilization():
    """
    USED ThreadPoolExecutor to speed up the detection process
    """
    # Run every hour, will need to ping all unassigned ip address
    # from iprequest.models import IPRequest
    from accounts.views import _greeting
    from ippool.models import IPAddressPool, IllegalIPDetectection, IllegalHostDetection
    from iprequest.models import IPRequest, MacAddress
    import ipMgntSystemSettings.settings as my_settings
    unassigned_ip_list = IPAddressPool.objects.filter(ip_status=UNASSIGNED)
    ip_objs = [ResolveMac(unassigned_ip.ip_address)
               for unassigned_ip in list(unassigned_ip_list)]
    pool_ping = ThreadPoolExecutor(max_workers=20)
    for ip_obj in ip_objs:
        pool_ping.submit(ip_obj.get_mac)
    pool_ping.shutdown(wait=True)
    for ip_obj in ip_objs:
        if ip_obj.mac:
            unassigned_ip = unassigned_ip_list.get(ip_address=ip_obj.ip)

            # create IllegalHostDetection
            
            detection_date = time.strftime("%Y%m%d")
            illegal_host_mac = ip_obj.mac
            illegal_host_mac_vendor = get_mac_vendor(illegal_host_mac)
            print(f"[+] Illegal IP {ip_obj.ip} with MAC <<{illegal_host_mac}>> detected!")
            new_illegal_host = IllegalHostDetection.objects.create(
                mac_address=illegal_host_mac,
                mac_address_vendor=illegal_host_mac_vendor,
            )
            new_illegal_host.save()
            detection_id = str(detection_date) + str(new_illegal_host.id)
            new_illegal_host.detection_id = detection_id
            new_illegal_host.save()

            # Reveal the owner if the mac is on the db
            try:
                illegal_owner = MacAddress.objects.get(mac=illegal_host_mac)
            except MacAddress.DoesNotExist: 
                pass
            else:
                print(f"[+] {illegal_owner.ip_request.stuff_user} is illegally using IP {ip_obj.ip}!")
                new_illegal_host.reveal_owner = illegal_owner.ip_request.stuff_user
                #Send Email to Illegal Owner
                try:
                    mail_subject = f'Illegal IP { unassigned_ip.ip_address } utilization detection notice 😭'
                    recipents = my_settings.MANAGER_EMAIL.append(illegal_owner.ip_request.stuff_user)
                    message = get_template(
                        'emails/illegal_ip_utilization_notice_email.html').render({
                            'unassigned_ip': unassigned_ip,
                            'new_illegal_host': new_illegal_host,
                            'greeting': _greeting(),
                            
                        })
                    send_email = EmailMessage(to=recipents,
                                            subject=mail_subject, body=message)

                    send_email.content_subtype = 'html'
                    send_email.send(fail_silently=False)
                    print(f"[+] Warning email sent to {illegal_owner.ip_request.stuff_user} to release IP {ip_obj.ip}!")

                except:
                    print("The system failed to notify the illegal owner via email..")

            

            # add to IllegalIPDetectection
            try:
                illegal_ip_address = IllegalIPDetectection.objects.get(
                    illegal_ip=unassigned_ip)
                
            except IllegalIPDetectection.DoesNotExist:
                illegal_ip_address = IllegalIPDetectection.objects.create(
                    illegal_ip=unassigned_ip,
                )
            else:
                illegal_ip_address.latest_update = timezone.now()  # datetime.datetime.now()
            finally:
                print(f"[+] Added illegal IP {ip_obj.ip} & MAC <<{illegal_host_mac}>> to the database!")
                illegal_ip_address.illegal_hosts.add(new_illegal_host)
                illegal_ip_address.save()


logo = """
------------------------------------------------------------------------------------------------------------
  ___ _     _     _____ ____    _    _       ___ ____    ____  _____ _____ _____ ____ _____ ___ ___  _   _ 
 |_ _| |   | |   | ____/ ___|  / \  | |     |_ _|  _ \  |  _ \| ____|_   _| ____/ ___|_   _|_ _/ _ \| \ | |
  | || |   | |   |  _|| |  _  / _ \ | |      | || |_) | | | | |  _|   | | |  _|| |     | |  | | | | |  \| |
  | || |___| |___| |__| |_| |/ ___ \| |___   | ||  __/  | |_| | |___  | | | |__| |___  | |  | | |_| | |\  |
 |___|_____|_____|_____\____/_/   \_\_____| |___|_|     |____/|_____| |_| |_____\____| |_| |___\___/|_| \_|
                                                                                                           
============================================================================================================
"""

if __name__ == '__main__':
    print(logo)
    print("Running now...")
    while True:
        print(f"[{datetime.datetime.today()}]-Started new illegal utilization IP scan... " )
        detect_illegal_ip_utilization()
        print(f"[{datetime.datetime.today()}]-Ended scan \n\n\nRunning..." )
        sleep(30)
