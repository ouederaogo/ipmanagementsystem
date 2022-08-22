import os
import django
import ipaddress

os.environ.setdefault('DJANGO_SETTINGS_MODULE',
                      'ipMgntSystemSettings.settings')
django.setup()
#++++++++++++++++++++++++++++++++++++++++++++#


def push_ip_to_database():
    from ippool.models import IPAddressPool
    ip_range = [str(ip) for ip in ipaddress.IPv4Network('192.168.1.0/28')]
    for ip in ip_range:
        ip_address = IPAddressPool()
        ip_address.ip_address = ip
        ip_address.save()
    print("\n\n#######################\nIP addresses successfull saved")


if __name__ == '__main__':
    push_ip_to_database()
