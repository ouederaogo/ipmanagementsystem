from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.timezone import make_aware
from ippool.models import IPAddressPool
from accounts.models import Account
import datetime
from django.core.validators import MinValueValidator, MaxValueValidator


# Create your models here.

class IPRequest(models.Model):
    NEW = 'new'
    ACCEPTED = 'accepted'
    REJECTED = 'rejected'
    EXPIRED = 'expired'

    REQUEST_STATUS_CHOICES = (
        (NEW, NEW),
        (ACCEPTED, ACCEPTED),
        (REJECTED, REJECTED),
        (EXPIRED, EXPIRED),
    )
    stuff_user =models.ForeignKey(
        Account, null=True, blank=True, related_name='stuff_user', on_delete=models.SET_NULL)
    request_id = models.CharField(max_length=10, blank=True)
    number_of_ip = models.IntegerField( validators=[MinValueValidator(1), MaxValueValidator(30)], default=1)
    comment = models.TextField(max_length=500, null=True, blank=True)
    request_date = models.DateTimeField(auto_now_add=True)  # default=timezone.now
    lease_start = models.DateTimeField(auto_now_add=True)
    lease_end = models.DateField()
    lease_end_midnight = models.DateTimeField( null=True, blank=True)
    
    assigned_ip = models.ManyToManyField( IPAddressPool,blank=True)
    approved_date = models.DateTimeField(null=True, blank=True)
    # IMPORTANT: Need to change this user later
    approved_by = models.ForeignKey(
        Account, null=True, blank=True, related_name='approved_by', on_delete=models.SET_NULL)
    request_status = models.CharField(
        max_length=50, choices=REQUEST_STATUS_CHOICES, default=NEW)
    is_rejected = models.BooleanField(default=False, blank=True)
    rejection_reason = models.TextField(max_length=500, null=True, blank=True)
    notify = models.BooleanField(default=False)
    requestor_ip = models.CharField(max_length=15, null=True, blank=True)
    extend = models.IntegerField( validators=[MinValueValidator(0), MaxValueValidator(4)], default=0, blank=True, null=True )
    
    def save(self, *args, **kwargs):
        self.lease_end_midnight = make_aware(
            datetime.datetime(self.lease_end.year, self.lease_end.month, self.lease_end.day, 23, 59,  59)
            )
        return super().save(*args, **kwargs)
        

    def __str__(self):
        return f"{self.request_id}{self.stuff_user}: { 'ip-assigned' if self.assigned_ip else 'No-ip-assign'} | {self.request_status}"

    def get_request_detail_url(self):
        return reverse('pending_ip_request_detail', args=[self.request_id])

    def status_color(self):  # for boostrap class
        if self.request_status == self.ACCEPTED:
            return 'success'
        elif self.request_status == self.EXPIRED:
            return 'danger'
    def get_request_status(self):
        today_date = datetime.datetime.today().date()
        return "still assigned" if self.lease_end > today_date else "exipred"
       


    class Meta:
        ordering = ("-request_date", )
        verbose_name = 'IP Request'
        verbose_name_plural = "IP Requests"


class MacAddress(models.Model):
    ip_request= models.ForeignKey(IPRequest, null=True, blank=True,  on_delete=models.SET_NULL)
    mac = models.CharField(max_length=20, unique=True, blank=True, null=True)
    mac_vendor = models.CharField(max_length=100, null=True, blank=True)
    detected_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    def __str__(self):
        return f"{self.ip_request.stuff_user}: {self.mac}"
    
    class Meta:
        ordering = ("-detected_at", )
        verbose_name = 'Mac Address'
        verbose_name_plural = "Mac Addresses"