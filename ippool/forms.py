from django import forms
from .models import IPAddressPool


class IPAddressPoolForm(forms.ModelForm):
    class Meta:
        model = IPAddressPool
        fields = (
            'ip_address',
            'ip_status',
        )

    def __init__(self, *args, **kwargs):
        super(IPAddressPoolForm, self).__init__(*args, **kwargs)
        self.fields['ip_address'].widget.attrs['placeholder'] = 'Enter IP address..'
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'

 
