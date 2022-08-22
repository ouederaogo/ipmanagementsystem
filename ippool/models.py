from django.db import models
from django.utils import timezone
from django.template.defaultfilters import slugify
from django.urls import reverse
from accounts.models import Account


# Create your models here.

# https://stackoverflow.com/questions/48600413/how-to-change-value-of-choice-field-in-django-shell
# https://stackoverflow.com/questions/41036216/how-to-render-form-choices-manually
class IPAddressPool(models.Model):
    UNASSIGNED = 'unassigned'
    ASSIGNED = 'assigned'
    RESERVED = 'reserved'
    STATUS_CHOICES = (
        (UNASSIGNED, UNASSIGNED),
        (ASSIGNED, ASSIGNED),
        (RESERVED, RESERVED),
    )
    ip_address = models.GenericIPAddressField( protocol='both')
    ip_status = models.CharField(max_length=50, choices=STATUS_CHOICES, default=UNASSIGNED)
    added_date = models.DateTimeField(auto_now_add=True)
    added_by = models.ForeignKey(Account, null=True, blank=True, on_delete=models.SET_NULL)
    slug = models.SlugField(max_length=15, unique=True,blank=True) 

    def status_color(self):  # for boostrap class
        if self.ip_status == self.UNASSIGNED:
            return 'success'
        elif self.ip_status == self.ASSIGNED:
            return 'danger'
        elif self.ip_status == self.RESERVED:
            return 'secondary'

    def __str__(self):
        return f"{self.ip_address}: {self.ip_status}"

    class Meta:
        ordering = ("ip_address", )
        verbose_name = 'IP Address Pool'
        verbose_name_plural = "IP Address Pool"

    def save(self, *args, **kwargs):
        self.slug = slugify(f'{self.ip_address.replace(".", "_")}')
        return super().save(*args, **kwargs)


class IPReport(models.Model):
    report_id = models.CharField(max_length=10, blank=True)
    generated_by = models.ForeignKey(
        Account, null=True, blank=True, on_delete=models.SET_NULL)
    generated_date = models.DateTimeField(auto_now_add=True)
    report = models.FileField(upload_to='reports/', null=True, blank=True,)
    send_to = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return self.report_id

    class Meta:
        ordering = ("-generated_date", )
        verbose_name = 'IP Report'
        verbose_name_plural = "IP Reports"


class IllegalHostDetection(models.Model):
    detection_id = models.CharField(max_length=10, blank=True)
    mac_address_vendor = models.CharField(
        max_length=100)
    mac_address = models.CharField(max_length=20)
    detected_time = models.DateTimeField(default=timezone.now)
    reveal_owner = models.ForeignKey(
        Account, null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return self.mac_address

    class Meta:
        ordering = ("-detected_time", )
        verbose_name = 'Illegal Host Detection'
        verbose_name_plural = "Illegal Hosts Detection"


class IllegalIPDetectection(models.Model):
    illegal_ip = models.ForeignKey(
        IPAddressPool, null=True, on_delete=models.CASCADE)
    illegal_hosts = models.ManyToManyField(IllegalHostDetection, blank=True)
    latest_update = models.DateTimeField(
        default=timezone.now)

    def __str__(self):
        return self.illegal_ip.ip_address

    class Meta:
        ordering = ("-latest_update", )
        verbose_name = 'Illegal IP Detectection'
        verbose_name_plural = "Illegal IPs Detectection"
