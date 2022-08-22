from django import forms
from .models import IPRequest


class IPRequestForm(forms.ModelForm):
    class Meta:
        model = IPRequest
        fields = (
            'number_of_ip',
            'lease_end',
            'comment',
        )

    def __init__(self, *args, **kwargs):
        super(IPRequestForm, self).__init__(*args, **kwargs)
        self.fields['number_of_ip'].widget.attrs[
            'placeholder'] = 'Number of IPs '
        self.fields['lease_end'].widget.attrs[
            'placeholder'] = 'Lease due date(YYYY-MM-DD)'
        self.fields['comment'].widget.attrs[
            'placeholder'] = 'Comments'

        # self.fields['first_name'].widget.attrs['class'] = 'form-control'
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'
