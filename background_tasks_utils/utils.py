import subprocess
import platform
import requests
import scapy.all as scapy


class PingDiagnostic:
    def __init__(self, ip):
        self.ip = ip
        self.is_reachable = False

    def ping(self):
        """Test the IP range reachability"""
        # User to test ip reachability in Windows system
        if platform.system().lower() == "windows":
            p = subprocess.Popen(["ping", "-n", "2", self.ip],
                                 stdout=subprocess.PIPE).communicate()[0]
            if "unreachable" not in str(p):
                # print(self.ip + " is USED!")
                self.is_reachable = True
                return self.is_reachable
        else:
            # Used to test ip reachability in Linux system
            p = subprocess.Popen(
                ['ping', self.ip, '-c', '1', "-W", "4"], stdout=subprocess.PIPE)
            p.wait()
            if p.poll() == 0:
                # print(self.ip + " is USED!")
                self.is_reachable = True
                return self.is_reachable

    def __str__(self):
        return f"{self.ip}-{self.is_reachable}"




class ResolveMac:
    def __init__(self, ip):
        self.ip = ip
        self.mac = None
    
    def get_mac(self):
        arp_content = scapy.ARP(pdst=self.ip)
        l2_head = scapy.Ether(dst="ff:ff:ff:ff:ff:ff")
        arp_request = l2_head / arp_content
        answered_list = scapy.srp(arp_request, timeout=1, verbose=False)[0]
        if answered_list:
            self.mac = answered_list[0][1].hwsrc



def get_mac(ip):
    arp_content = scapy.ARP(pdst=ip)
    l2_head = scapy.Ether(dst="ff:ff:ff:ff:ff:ff")
    arp_request = l2_head / arp_content
    # print(arp_request.show())
    answered_list = scapy.srp(arp_request, timeout=1, verbose=False)[0]

    if answered_list:
        return answered_list[0][1].hwsrc


def get_mac_vendor(mac_address):
    # We will use an API to get the vendor details
    url = "https://api.macvendors.com/"
    # Use get method to fetch details
    response = requests.get(url + mac_address)
    if response.status_code != 200:
        # raise Exception("[!] Invalid MAC Address!")
        return 'Unknown'
    return response.content.decode()
