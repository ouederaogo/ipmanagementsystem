from django.shortcuts import render, redirect
from django.contrib import messages, auth
from django.contrib.auth.decorators import login_required
from accounts.models import Account
from .forms import RegistrationForm
import datetime
import requests

# Nessary import to send email.
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import get_template
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage

# Create your views here.


def _greeting():
    currentTime = datetime.datetime.now()
    if currentTime.hour < 12:
        return 'Good morning'
    elif 12 <= currentTime.hour < 18:
        return 'Good afternoon'
    else:
        return 'Good evening'


def register(request):

    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            print(form.cleaned_data)
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            phone_number = form.cleaned_data['phone_number']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            username = email.split('@')[0]
            user = Account.objects.create_user(
                first_name=first_name,
                last_name=last_name,
                email=email,
                username=username,
                password=password,
            )
            user.phone_number = phone_number
            user.save()

            # USER ACTIVATION
            current_site = get_current_site(request)
            mail_subject = ' Please Activate your TSEManagementSystem Account'

            message = get_template(
                'accounts/account_verification_email.html').render({
                    'user': user,
                    'domain': current_site,
                    'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                    'token': default_token_generator.make_token(user),
                    'greeting': _greeting(),
                })
            to_email = email
            send_email = EmailMessage(mail_subject, message, to=[to_email])
            send_email.content_subtype = 'html'
            send_email.send(fail_silently=False)
            # USER ACTIVATION END

            # messages.success(
            #     request, 'Thanks for registering with us. We have sent you a verification email to your email address. Please verify it.')
            return redirect('/accounts/login/?command=verification&email=' + email)

            # # messages.success(
            # #     request, f"Registration successfull.")
            # return redirect('register')
    else:
        form = RegistrationForm()
    context = {
        'form': form,
    }
    return render(request, 'accounts/register.html', context)


def login(request):
    if request.user.is_authenticated:
        messages.success(
            request, f'{_greeting()} {request.user.first_name}, You are currently already logged in!')
        return redirect('ip_address_pool')

    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        # return the user object if exists
        user = auth.authenticate(email=email, password=password)
        if user is not None:
            auth.login(request, user)
            messages.success(
                request, f'{_greeting()} {user.first_name}, You are logged in.')

            if request.user.is_authenticated:
                # Redirect user to proper page--START
                url = request.META.get('HTTP_REFERER')
                try:
                    query = requests.utils.urlparse(url).query
                    # print('\n\nQuery-->', query)  # Query--> next=/cart/checkout/
                    params = dict(x.split('=') for x in query.split('&'))
                    # print('\nParams-->', params)  # {'next': '/cart/checkout/'}
                    if 'next' in params:
                        nextPage = params['next']
                        return redirect(nextPage)
                except:
                    if request.user.is_admin:
                        return redirect('ip_address_pool')
                    else:
                        return redirect('my_ip_lease_records')
                # Redirect user to proper page--END
            else:
                return redirect('home')
        else:
            messages.error(request, 'Sorry, invalid login credenticals!')
            return redirect('login')
    return render(request, 'accounts/login.html')


@login_required(login_url='login')
def logout(request):
    auth.logout(request)
    messages.success(
        request, f'You are logged out, Bye.')
    return redirect('login')


def activate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = Account._default_manager.get(pk=uid)
    except (TypeError, ValueError, OverflowError, Account.DoesNotExist):
        user = None
    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(
            request, f"{_greeting()} {user.first_name}. Congratulation! Your Account is activated. You sould be able to login to your account.")
        return redirect('login')
    else:
        messages.error(request, "Sorry! Invaid activation link")
        return redirect('register')


def forgotPassword(request):
    if request.method == 'POST':
        email = request.POST['email']
        if Account.objects.filter(email=email).exists():
            user = Account.objects.get(email__exact=email)
            # Reset password email
            current_site = get_current_site(request)
            mail_subject = 'Reset your TSEManagementSystem Account Password'

            message = get_template('accounts/reset_password_email.html').render({
                'user': user,
                'domain': current_site,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
                'greeting': _greeting(),
            })
            to_email = email
            send_email = EmailMessage(mail_subject, message, to=[to_email])
            send_email.content_subtype = 'html'
            send_email.send(fail_silently=False)
            # Reset password email END
            messages.success(
                request, f"Password reset email has been sent to your email address {email}. Please use the link included in the email to reset your password!")
            return redirect('login')

        else:
            messages.error(request, "Account does not exist")
            return redirect('forgotPassword')
    return render(request, 'accounts/forgotPassword.html')


def resetpassword_validate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = Account._default_manager.get(pk=uid)
    except (TypeError, ValueError, OverflowError, Account.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        request.session['uid'] = uid
        messages.success(request, "Please reset your password")
        return redirect('resetPassword')
    else:
        messages.error(request, "Sorry! this link has been expired")
        return redirect('login')


def resetPassword(request):
    if request.method == 'POST':
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']
        if password == confirm_password:
            uid = request.session.get('uid')
            user = Account.objects.get(pk=uid)
            user.set_password(password)
            user.save()
            messages.success(
                request, f"{_greeting()} {user.first_name}. Your password reset is successfull. Please use the newly created password to login. Thanks!")
            return redirect('login')
        else:
            messages.error(request, 'Sorry, passowrd do not match.')
            return redirect('resetPassword')
    else:
        return render(request, 'accounts/resetPassword.html')
