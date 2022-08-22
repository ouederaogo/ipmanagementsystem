from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.paginator import Paginator
from django.utils import timezone
from django.template.loader import get_template
from django.core.mail import EmailMessage
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.contrib.sites.shortcuts import get_current_site
import datetime
import time

import ipMgntSystemSettings.settings as my_settings

# Create your views here.
from .models import IPRequest
from .forms import IPRequestForm
from ippool.models import IPAddressPool
from accounts.views import _greeting


def generate_id(object):
    # Need to generate and  save the request_id:
    yr = int(datetime.date.today().strftime('%Y'))
    dt = int(datetime.date.today().strftime('%d'))
    mt = int(datetime.date.today().strftime('%m'))
    d = datetime.date(yr, mt, dt)
    current_date = d.strftime("%Y%m%d")  # 20210305
    return current_date + str(object.id)

# Form for user to send they request
@login_required(login_url='login')
def apply_new_ip_address(request):
    # print(request.user.is_authenticated)
    if request.user.is_authenticated:
        form = IPRequestForm()
        if request.method == 'POST':
            form = IPRequestForm(request.POST)
            if form.is_valid():
                new_request = form.save(commit=False)
                new_request.requestor_ip = request.META.get("REMOTE_ADDR")
                new_request.stuff_user = request.user

                # NEED TO CHECK THAT THE LEASE END is greater that today
                lease_end_date = form.cleaned_data['lease_end']
                today_date = datetime.datetime.today().date()
                if lease_end_date < today_date:
                    messages.warning(
                        request, f"Sorry {new_request.stuff_user.first_name}! Your request failed. The lease due date  {lease_end_date} is wrong. Please note that the lease due date can't be less that today date {today_date}. Please try again with correct due lease due date!")
                    return redirect('apply_new_ip_address')
                else:
                    new_request.save()
                    new_request.request_id = generate_id(new_request)
                    new_request.save()

                    # NOTIFY the manger manager via email about new request
                    current_site = get_current_site(request)
                    mail_subject = f'TSEManagementSystem NEW IP ADDRESS REQUESTED BY { new_request.stuff_user.first_name.upper() } NOTICE📢'
                    message = get_template(
                        'emails/new_ip_request_notice_email.html').render({
                            'new_request': new_request,
                            'domain': current_site,
                            'greeting': _greeting()
                        })
                    send_email = EmailMessage(to=my_settings.MANAGER_EMAIL,
                                            subject=mail_subject, body=message)

                    send_email.content_subtype = 'html'
                    send_email.send(fail_silently=False)

                    context = {
                        'new_request': new_request,
                    }
                    return render(request, 'iprequest/apply_new_ip_address_success_messaage.html', context)
        context = {
            'form': form
        }
        return render(request, 'iprequest/apply_new_ip_address.html', context)
    else:
        return redirect('home')


# To view new IP requests list
@login_required(login_url='login')
def pending_ip_requests(request):
    if request.user.is_admin:
        ip_requests = IPRequest.objects.filter(request_status='new')
        context = {
            'ip_requests': ip_requests
        }
        return render(request, 'iprequest/pending_ip_requests.html', context)
    else:
        messages.error(
                    request, f"Sorry, this action is only restricted to Administrators.")
        return redirect('home')


# view new request detail
@login_required(login_url='login')
def pending_ip_request_detail(request, request_id):
    if request.user.is_admin:
        # IP address status
        UNASSIGNED = 'unassigned'
        ASSIGNED = 'assigned'
        RESERVED = 'reserved'

        # Request status
        NEW = 'new'
        ACCEPTED = 'accepted'
        REJECTED = 'rejected'
        EXPIRED = 'expired'

        new_request = IPRequest.objects.get(request_id=request_id)
        approval = request.GET.get('approval').lower() if request.GET.get(
            'approval') != None else ''

        # Ensure that the  request haven't approved yet #START
        accepted_ip_requests = IPRequest.objects.filter(
            request_status=ACCEPTED)
        rejected_ip_requests = IPRequest.objects.filter(
            request_status=REJECTED)

        # Ensure that the  request haven't approved yet #END
        if approval == ACCEPTED:
            # Ensure that that request haven't approved yet #START
            if accepted_ip_requests.filter(request_id=request_id).exists():
                messages.warning(
                    request, f"Sorry! The request #{request_id} is already approved. Please check the  accepted requests list below. Thanks!")
                return redirect('ip_requests_list')

            if rejected_ip_requests.filter(request_id=request_id).exists():
                messages.warning(
                    request, f"Sorry! The request #{request_id} is already rejected. Please check the request rejected requests list below. Thanks!")
                return redirect('request_rejected_list')
            # Ensure that that request haven't approved yet #END
            # If the request is not approved then do below actions
            # NEED TO CHECK THAT THE LEASE END is greater that today, else reject the request
            lease_end_date = new_request.lease_end
            today_date = datetime.datetime.today().date()

            if lease_end_date < today_date:
                messages.warning(
                    request, f"Sorry! You can approved the request #{new_request.request_id}. The lease  date  {lease_end_date} already expired. Please kindly help to reject and  info {new_request.stuff_user.first_name.upper()} {new_request.stuff_user.last_name.upper()} to re-submit a new ip request. Thanks!")
                return redirect('pending_ip_request_detail', request_id=new_request.request_id)

            unassigned_ip_address = IPAddressPool.objects.filter(
                ip_status=UNASSIGNED)

            #Ensure that the number of reminded Ip address is greater than the requeseted number of ip
            if unassigned_ip_address.exists() and len(list(unassigned_ip_address))>=new_request.number_of_ip:
                # TODO:Selected a range of Ip address based on user number_of_ip 
                selected_ip_list = list(unassigned_ip_address)[:new_request.number_of_ip]

                # TODO: Send IP address to via email
                try:

                    mail_subject = f'TSEManagementSystem request #{new_request.request_id} IP ALLOCATED UNTIL {new_request.lease_end} 🎁'

                    message = get_template(
                        'emails/ip_allocate_email.html').render({
                            'new_request': new_request,
                            'selected_ip_list': selected_ip_list,
                            'greeting': _greeting(),

                        })

                    send_email = EmailMessage(
                        mail_subject, message, to=[new_request.stuff_user.email])
                    send_email.content_subtype = 'html'
                    send_email.send(fail_silently=False)

                except Exception as e:
                    # SMTPAuthenticationError
                    messages.warning(
                        request, f"Email sending failed... The system is unable to approve the request #{new_request.request_id} due to admin email ‘Bad Credentials’ or remote server ‘lost connection’. Please ensure that the admin email credentials are correct, and the remote PC is connected to internet, then try again!")
                    return redirect('pending_ip_requests')
                else:
                    for selected_ip in selected_ip_list:
                        new_request.assigned_ip.add(selected_ip)
                        # TODO: Update the allocated ip status from unassigned to assign
                        selected_ip.ip_status = ASSIGNED
                        selected_ip.save()
                    new_request.request_status = ACCEPTED
                    new_request.approved_by = request.user
                    new_request.approved_date = datetime.datetime.now()
                    new_request.save()

                # TODO: return success message
                context = {
                    'new_request': new_request,
                    'selected_ip_list': selected_ip_list,
                }
                return render(request, 'iprequest/pending_ip_request_approval_accept.html', context)
            else:
                messages.warning(
                    request, f"The system can  NOT APPROVED the request #{new_request.request_id} due to IP address pool  exhausted. Please ensure that the IP address pool has available IP address, then try again!")
                return redirect('pending_ip_request_detail', request_id=new_request.request_id)
                # messages.success("CAN NOT APPROVED due to Ip address pool  exhaution")
                # return redirect('same_page')

        elif approval == REJECTED:
            # Ensure that the  request haven't approved yet #START
            if accepted_ip_requests.filter(request_id=request_id).exists():
                messages.warning(
                    request, f"Sorry! The request #{request_id} is already approved. Please check the request accepted list below. Thanks!")
                return redirect('ip_requests_list')

            if rejected_ip_requests.filter(request_id=request_id).exists():
                messages.warning(
                    request, f"Sorry! The request #{request_id} is already rejected. Please check the request reject request list below. Thanks!")
                return redirect('request_rejected_list')
            # Ensure that the  request haven't approved yet #END

            #Handle the rejection
            # Request status
            NEW = 'new'
            ACCEPTED = 'accepted'
            REJECTED = 'rejected'
            EXPIRED = 'expired'

            # new_request = IPRequest.objects.get(request_id=request_id)
            if request.method == 'POST':
                try:
                    rejection_reason = request.POST['rejection_reason']
                except:
                    # KeyError error
                    messages.warning(
                        request, f"The system is unable to cancel the request #{new_request.request_id} due rejection reason empty. Please ensure that you enter the reason, then try again!")
                    return redirect('pending_ip_request_detail', request_id=new_request.request_id)

                # TODO: Send email to info the rejection reason
                try:
                    mail_subject = f'TSEManagementSystem IP ADDRESS LEASE #{new_request.request_id} REJECTION 😪'
                    message = get_template(
                        'emails/ip_request_rejection_email.html').render({
                            'new_request': new_request,
                            'rejection_reason': rejection_reason,
                            'greeting': _greeting()
                        })

                    send_email = EmailMessage(
                        mail_subject, message, to=[new_request.stuff_user.email])
                    send_email.content_subtype = 'html'
                    send_email.send(fail_silently=False)
                except:
                    # SMTPAuthenticationError
                    messages.warning(
                        request, f"Email sending failed... The system is unable to cancel the request #{new_request.stuff_user.request_id} due to admin email ‘Bad Credentials’ or remote server ‘lost connection’. Please ensure that the admin email credentials are correct, and the remote PC is connected to internet, then try again!")
                    return redirect('pending_ip_requests')

                # TODO: update the new request_status,  approved_by, approved_date
                new_request.request_status = REJECTED
                new_request.approved_date = datetime.datetime.now()
                new_request.is_rejected = True
                new_request.rejection_reason = rejection_reason
                new_request.approved_by = request.user  # need to complete later
                new_request.save()

                context = {'new_request': new_request}
                return render(request, 'iprequest/pending_ip_request_rejction_complete.html', context)
                #-----


            context = {
                'new_request': new_request
            }
            return render(request, 'iprequest/pending_ip_request_reject_reason.html', context)

        context = {
            'new_request': new_request,
            'is_already_accepted': accepted_ip_requests.filter(request_id=request_id).exists(),
            'is_already_rejected': rejected_ip_requests.filter(request_id=request_id).exists(),
        }
        return render(request, 'iprequest/pending_ip_request_detail.html', context)
    else:
        messages.error(
                    request, f"Sorry, this action is only restricted to Administrators.")
        return redirect('home')





# APPROVED IP request valid and expired list
@login_required(login_url='login')
def ip_requests_list(request):
    if request.user.is_admin:
        # Request status
        NEW = 'new'
        ACCEPTED = 'accepted'
        REJECTED = 'rejected'
        EXPIRED = 'expired'
        request_status = request.GET.get('request_status').lower() if request.GET.get(
            'request_status') != None else 'all'
        ip_request_list = IPRequest.objects.all()
        if request_status == 'valid':
            approved_request_list = ip_request_list.filter(
                Q(request_status=ACCEPTED))
        elif request_status == 'expired':
            approved_request_list = ip_request_list.filter(
                Q(request_status=EXPIRED))
        else:  # 'all' other cases
            approved_request_list = ip_request_list.filter(
                Q(request_status=ACCEPTED) | Q(request_status=EXPIRED) )

        # requests count
        request_valid_count = ip_request_list.filter(
            Q(request_status=ACCEPTED)).count()
        request_expired_count = ip_request_list.filter(
            Q(request_status=EXPIRED)).count()

        # compute the request per month statistic
        current_year = datetime.date.today().strftime('%Y')
        current_month = datetime.date.today().strftime('%m')
        jan = current_year + '01'
        feb = current_year + '02'
        mar = current_year + '03'
        apr = current_year + '04'
        may = current_year + '05'
        jun = current_year + '06'
        jul = current_year + '07'
        aug = current_year + '08'
        sep = current_year + '09'
        oct = current_year + '10'
        nov = current_year + '11'
        dec = current_year + '12'

        months_ids = [jan, feb, mar, apr, may,
                      jun, jul, aug, sep, oct, nov, dec]
        until_now_months_ids = months_ids[:int(current_month)]
        requests_stats_per_month = ''
        for month_id in until_now_months_ids:
            req_num = ip_request_list.filter(
                request_id__startswith=month_id).count()
            requests_stats_per_month += f"{req_num},"

        # labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
        #           "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

        paginator = Paginator(approved_request_list, 100)
        page_number = request.GET.get('page')
        approved_requests = paginator.get_page(page_number)

        context = {
            'approved_request_list': approved_requests,
            'request_valid_count': request_valid_count,
            'request_expired_count': request_expired_count,
            'requests_stats_per_month': requests_stats_per_month,
            'request_status': request_status,
        }
        return render(request, 'iprequest/ip_requests_list.html', context)
    else:
        messages.error(
                    request, f"Sorry, this action is only restricted to Administrators.")
        return redirect('home')


# IP request canceled (Non approved) list
@login_required(login_url='login')
def request_rejected_list(request):
    if request.user.is_admin:
        REJECTED = 'rejected'
        rejected_requests = IPRequest.objects.filter(request_status=REJECTED)

        paginator = Paginator(rejected_requests, 20)
        page_number = request.GET.get('page')
        rejected_requests = paginator.get_page(page_number)

        context = {
            'rejected_requests': rejected_requests,
        }
        return render(request, 'iprequest/request_rejected_list.html', context)
    else:
        return redirect('home')


# help user return they ip request history based on email
@login_required(login_url='login')
def my_ip_lease_records(request):
    if request.user.is_authenticated:
        # Extend lease_end request
        request_id = request.GET.get('request_id').lower() if request.GET.get(
            'request_id') != None else ''
        if request_id:
            MAX_EXTEND_TIME = 4
            EXTEND_FOR = 7 #day
            try:
                request_to_extend = IPRequest.objects.get(request_id=request_id)
            except IPRequest.DoesNotExist:
                messages.error(
                    request, f"Sorry, the request #{request_id} can't be found!")
            else:
                if request_to_extend.extend < MAX_EXTEND_TIME:
                    new_lease_end = datetime.datetime.strptime(f"{request_to_extend.lease_end}","%Y-%m-%d") + datetime.timedelta(days=EXTEND_FOR)
                    request_to_extend.lease_end = new_lease_end
                    request_to_extend.extend +=1
                    request_to_extend.save()

        stuff_user = request.user
        my_ip_record_list = IPRequest.objects.filter(stuff_user=stuff_user)

        paginator = Paginator(my_ip_record_list, 20)
        page_number = request.GET.get('page')
        my_ip_records = paginator.get_page(page_number)
        context = {
                'my_ip_records': my_ip_records,
            }

        return render(request, 'iprequest/my_ip_lease_records.html', context)

    else:
        return redirect('home')
    




