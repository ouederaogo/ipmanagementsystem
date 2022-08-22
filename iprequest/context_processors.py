from .models import IPRequest


def new_ip_requests(request):
    new_requests_processors = IPRequest.objects.filter(request_status='new')

    return dict(new_requests_processors=new_requests_processors)
