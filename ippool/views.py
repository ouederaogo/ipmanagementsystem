from django.shortcuts import redirect, render, get_object_or_404
from django.http import HttpResponse
from .models import IPAddressPool, IPReport, IllegalIPDetectection
from iprequest.models import IPRequest
from .forms import IPAddressPoolForm
from django.contrib import messages
from django.template.loader import render_to_string, get_template
from django.core.mail import EmailMessage
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.db.utils import IntegrityError
# Create your views here.
import os
import time
import csv
import ipaddress
from accounts.views import _greeting


@login_required(login_url='login')
def ip_address_pool(request):
    if request.user.is_admin:
        # IP address status
        UNASSIGNED = 'unassigned'
        ASSIGNED = 'assigned'
        RESERVED = 'reserved'
        # Query all the ip address from the DB
        all_ip_address_pool = IPAddressPool.objects.all()
        ip_status = request.GET.get('ip_status').lower() if request.GET.get(
            'ip_status') != None else 'all'

        if ip_status == UNASSIGNED:
            ip_address_pool = all_ip_address_pool.filter(ip_status=UNASSIGNED)
        elif ip_status == ASSIGNED:
            ip_address_pool = all_ip_address_pool.filter(ip_status=ASSIGNED)
        elif ip_status == RESERVED:
            ip_address_pool = all_ip_address_pool.filter(ip_status=RESERVED)
        else:
            ip_address_pool = all_ip_address_pool

        unassigned_ip_nums = all_ip_address_pool.filter(ip_status=UNASSIGNED).count
        assigned_ip_nums = all_ip_address_pool.filter(ip_status=ASSIGNED).count
        reserved_ip_nums = all_ip_address_pool.filter(ip_status=RESERVED).count

        # PAGINATING
        paginator = Paginator(ip_address_pool, 50)
        page_number = request.GET.get('page')
        ip_address_pool_page_obj = paginator.get_page(page_number)

        context = {
            'ip_status': ip_status,
            'unassigned_ip_nums': unassigned_ip_nums,
            'assigned_ip_nums': assigned_ip_nums,
            'reserved_ip_nums': reserved_ip_nums,
            'ip_address_pool': ip_address_pool_page_obj,

        }
        return render(request, 'ippool/ip_pool_list.html', context)
    else:
        return redirect('home')


@login_required(login_url='login')
def add_ip_address(request):
    if request.user.is_admin:
        form = IPAddressPoolForm()
        if request.method == 'POST':
            form = IPAddressPoolForm(request.POST)
            if form.is_valid():
                new_ip_address = form.save(commit=False)
                new_ip_address.added_by = request.user
                try:
                    new_ip_address.save()
                except IntegrityError:
                    messages.warning(
                        request, f"Sorry, IP  {new_ip_address.ip_address} address already existed in the address pool!")
                else:
                    messages.success(
                        request, f"IP  {new_ip_address.ip_address}/{new_ip_address.ip_status.upper()} is successfully added to address pool!")
                    return redirect('ip_address_pool')

        context = {
            'form': form
        }
        return render(request, 'ippool/add_ip_address.html', context)
    else:
        messages.error(
                    request, f"Sorry, this action is only restricted to Administrators.")
        return redirect('home')


@login_required(login_url='login')
def update_ip_address(request, slug):
    if request.user.is_admin:
        ip_address = IPAddressPool.objects.get(slug=slug)
        form = IPAddressPoolForm(request.POST or None,
                                 instance=ip_address)
        if request.method == 'POST':
            if form.is_valid():
                try:
                    form.save()
                except IntegrityError:
                    messages.warning(
                        request, f"Sorry, IP  {form.cleaned_data['ip_address']} address already existed in the address pool!")
                else:
                    messages.success(
                        request, f"IP  {form.cleaned_data['ip_address']}/{form.cleaned_data['ip_status'].upper()} is successfully updated!")
                    return redirect('ip_address_pool')
        context = {
            'form': form,
            'ip_address': ip_address,
        }
        return render(request, 'ippool/update_ip_address.html', context)
    else:
        messages.error(
                    request, f"Sorry, this action is only restricted to Administrators.")
        return redirect('home')


@login_required(login_url='login')
def delete_ip_address(request, slug):
    if request.user.is_admin:
        ip_address = get_object_or_404(IPAddressPool, slug=slug)
        # ip_address = IPAddressPool.objects.get(slug=slug)
        ip_address.delete()
        messages.success(
            request, f"IP address {ip_address.ip_address!r} is successfully removed from the address pool!")
        return redirect('ip_address_pool')
    else:
        messages.error(
                    request, f"Sorry, this action is only restricted to Administrators.")
        return redirect('home')


@login_required(login_url='login')
def delete_all_ip_from_pool(request):
    if request.user.is_admin:
        IPAddressPool.objects.all().delete()
        messages.warning(
            request, f"⚠️ All IP addresses have been removed from the IP Pool!")
        return redirect('ip_address_pool')
    else:
        messages.error(
                    request, f"Sorry, this action is only restricted to Administrators.")
        return redirect('home')


@login_required(login_url='login')
def generate_ip_report(request):
    if request.user.is_admin:
        time_str = time.strftime("%Y%m%d_%H%M%S")
        new_report_name = "ip-report-" + time_str + ".csv"

        # get the parent director path
        dir_path = os.path.dirname(os.path.dirname(__file__))
        reports_folder = os.path.join(dir_path, 'media/reports/')
        new_report_path = os.path.join(reports_folder, new_report_name)

        ip_pool = IPAddressPool.objects.all()
        try:
            with open(new_report_path, mode='w', newline='') as csv_file:
                fieldnames = ['IP', 'STATUS']
                writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
                writer.writeheader()
                for ip in ip_pool:
                    writer.writerow(
                        {'IP': ip.ip_address, 'STATUS': ip.ip_status})
        except:
            messages.warning(
                request, f"Sorry, the system is unable to generate the ip report")
            return redirect('ip_address_pool')
        # Save the file in the database
        if os.path.isfile(new_report_path):
            new_report = IPReport()
            new_report.report.name = f'reports/{new_report_name}'
            new_report.generated_by = request.user
            new_report.save()
            current_date = time.strftime("%Y%m%d")
            report_id = str(current_date) + str(new_report.id)
            new_report.report_id = report_id
            new_report.save()
        else:
            messages.warning(
                request, f"Sorry, the system can not find the generated report!")
            return redirect('ip_address_pool')

        messages.success(
            request, f"The IP report {new_report.report.name.split('/')[1]!r} is successfully generated and ready to send or download!")
        return redirect('send_ip_report', report_id=report_id)
    else:
        messages.error(
                    request, f"Sorry, this action is only restricted to Administrators.")
        return redirect('home')


@login_required(login_url='login')
def send_ip_report(request, report_id):
    if request.user.is_admin:
        report = IPReport.objects.get(report_id=report_id)
        if request.method == 'POST':
            try:
                send_to = request.POST['send_to']
            except KeyError:
                # KeyError error
                messages.warning(
                    request, f"The system is unable to send the ip report {report.report.name.split('/')[1]!r} due emails missing. Please ensure that you enter the email address list separate with comma, then try again!")
                return redirect('send_ip_report', report_id=report.report_id)
            else:
                if send_to:
                    # IP address status
                    UNASSIGNED = 'unassigned'
                    ASSIGNED = 'assigned'
                    RESERVED = 'reserved'
                    # Query all the ip address from the DB
                    all_ip_address_pool = IPAddressPool.objects.all()
                    unassigned_ip_nums = all_ip_address_pool.filter(
                        ip_status=UNASSIGNED).count
                    assigned_ip_nums = all_ip_address_pool.filter(
                        ip_status=ASSIGNED).count
                    reserved_ip_nums = all_ip_address_pool.filter(
                        ip_status=RESERVED).count
                    total_ip = all_ip_address_pool.count()

                    # send email
                    try:
                        receipts = send_to.split(',')
                        mail_subject = f"TSEManagementSystem IP REPORT {report.report.name.split('/')[1]}📃"

                        message = get_template(
                            'emails/send_ip_report_email.html').render({
                                'report': report,
                                'unassigned_ip_nums': unassigned_ip_nums,
                                'assigned_ip_nums': assigned_ip_nums,
                                'reserved_ip_nums': reserved_ip_nums,
                                'total_ip': total_ip,
                                'greeting': _greeting(),
                            })

                        send_email = EmailMessage(
                            mail_subject, message, to=receipts)
                        send_email.attach_file(report.report.path)
                        send_email.content_subtype = 'html'
                        send_email.send(fail_silently=False)

                        # Save the recipient email
                        report.send_to = send_to
                        report.save()
                    except Exception as e:
                        # print(e)
                        messages.warning(
                            request, f"Email sending failed... The system is unable to send the ip report#{report.report_id} due to admin email ‘Bad Credentials’ or remote server ‘lost connection’. Please ensure that the admin email credentials are correct, and the remote server is connected to internet, then try again!")
                        return redirect('send_ip_report', report_id=report.report_id)

                    context = {
                        'report': report,
                        'unassigned_ip_nums': unassigned_ip_nums,
                        'assigned_ip_nums': assigned_ip_nums,
                        'reserved_ip_nums': reserved_ip_nums,
                        'total_ip': total_ip,
                    }
                    return render(request, 'ippool/send_ip_report_complete.html', context)
            
        else:
            context = {'report': report}
            return render(request, 'ippool/send_ip_report.html', context)
    else:
        messages.error(
                    request, f"Sorry, this action is only restricted to Administrators.")
        return redirect('home')


@login_required(login_url='login')
def ip_report_list(request):
    if request.user.is_admin:
        report_list = IPReport.objects.all()
        context = {'report_list': report_list}
        return render(request, 'ippool/ip_report_list.html', context)
    else:
        messages.error(
                    request, f"Sorry, this action is only restricted to Administrators.")
        return redirect('home')


# return illegal ip list
@login_required(login_url='login')
def illegal_ip_detected_list(request):
    if request.user.is_admin:
        illegal_ips_list = IllegalIPDetectection.objects.all()
        context = {
            'illegal_ips_list': illegal_ips_list,
        }
        return render(request, 'ippool/illegal_ip_detected_list.html', context)
    else:
        return redirect('home')


@login_required(login_url='login')
def ip_addresses_history(request):
    if request.user.is_admin:
        ip_slug = request.GET.get('ip_slug') if request.GET.get(
            'ip_slug') else  None 
        
        ip_address_pool = list(IPAddressPool.objects.all())
        ip_request_list = list(IPRequest.objects.all())

        #Handle the situation where ip-addresses-history/?ip_slug=192_168_10_1
        if ip_slug:
            ip_address = IPAddressPool.objects.get(slug=ip_slug)
            lease_count = 0
            ip_address_leases = []
            for ip_request in ip_request_list:
                if ip_address in ip_request.assigned_ip.all():
                    lease_count +=1
                    ip_address_leases.append(ip_request)
            ip_address.lease_count = lease_count
            if ip_address_leases:
                list_of_ids = [ip_obj.id for ip_obj in ip_address_leases] #get the pk of al the history
                ip_address_leases = IPRequest.objects.filter(pk__in=list_of_ids).order_by('-request_date')
            
            context = {
                "ip_address": ip_address,
                "ip_address_leases": ip_address_leases,

            }
            return render(request, 'ippool/ip_addresses_history_detail.html', context)
            
        else: #Handle the situation where ip-addresses-history/
            
            if request.method == 'POST': #take care of the search
                try:
                    ip_address = request.POST['ip_address'].lower().strip()
                except Exception as e:
                    print(e)
                    # KeyError error
                    messages.warning(
                        request, f"The system return ip lease record due rejection email missing. Please ensure that you entered the  email, then try again!")
                    return redirect('ip_addresses_history')
                else:
                    ip_address_pool = list(IPAddressPool.objects.filter(ip_address=ip_address))
                 
            for ip_address in ip_address_pool:
                # count number of time that IP has been lease 
                lease_count = 0
                ip_address_leases = []
                for ip_request in ip_request_list:
                    if ip_address in ip_request.assigned_ip.all():
                        lease_count +=1
                        ip_address_leases.append(ip_request)
                ip_address.lease_count = lease_count
        
                # find the latest lease status
                if ip_address_leases:
                    list_of_ids = [ip_obj.id for ip_obj in ip_address_leases] #get the pk of al the history
                    latest_lease_request = IPRequest.objects.filter(pk__in=list_of_ids).order_by('-request_date').first()
                    ip_address.latest_request = latest_lease_request
            
            ip_address_pool = [ip_address_obj for ip_address_obj in ip_address_pool if ip_address_obj.lease_count>0 ] #filter lease_count=0
            context = {
                "ip_address_pool":sorted(ip_address_pool, key=lambda ip:ip.lease_count, reverse=True), #sort the list by count number


            }
            return render(request, 'ippool/ip_addresses_history_list.html', context)
    else:
        messages.error(
                    request, f"Sorry, this action is only restricted to Administrators.")
        return redirect('home')