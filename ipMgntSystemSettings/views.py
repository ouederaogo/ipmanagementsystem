from django.http import HttpResponse
from django.shortcuts import render
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django.template.loader import get_template


def home(request):
    return render(request, 'home.html')
