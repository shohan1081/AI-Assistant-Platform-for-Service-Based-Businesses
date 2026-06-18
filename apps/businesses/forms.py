from django import forms
from .models import Business
import json

DAYS_OF_WEEK = [
    'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'
]

class BusinessAdminForm(forms.ModelForm):
    # Define fields explicitly so Admin can find them in fieldsets
    Monday_active = forms.BooleanField(required=False, label="Monday")
    Monday_start = forms.CharField(required=False, label="From", widget=forms.TextInput(attrs={'placeholder': '9am', 'style': 'width: 100px;'}))
    Monday_end = forms.CharField(required=False, label="To", widget=forms.TextInput(attrs={'placeholder': '5pm', 'style': 'width: 100px;'}))

    Tuesday_active = forms.BooleanField(required=False, label="Tuesday")
    Tuesday_start = forms.CharField(required=False, label="From", widget=forms.TextInput(attrs={'placeholder': '9am', 'style': 'width: 100px;'}))
    Tuesday_end = forms.CharField(required=False, label="To", widget=forms.TextInput(attrs={'placeholder': '5pm', 'style': 'width: 100px;'}))

    Wednesday_active = forms.BooleanField(required=False, label="Wednesday")
    Wednesday_start = forms.CharField(required=False, label="From", widget=forms.TextInput(attrs={'placeholder': '9am', 'style': 'width: 100px;'}))
    Wednesday_end = forms.CharField(required=False, label="To", widget=forms.TextInput(attrs={'placeholder': '5pm', 'style': 'width: 100px;'}))

    Thursday_active = forms.BooleanField(required=False, label="Thursday")
    Thursday_start = forms.CharField(required=False, label="From", widget=forms.TextInput(attrs={'placeholder': '9am', 'style': 'width: 100px;'}))
    Thursday_end = forms.CharField(required=False, label="To", widget=forms.TextInput(attrs={'placeholder': '5pm', 'style': 'width: 100px;'}))

    Friday_active = forms.BooleanField(required=False, label="Friday")
    Friday_start = forms.CharField(required=False, label="From", widget=forms.TextInput(attrs={'placeholder': '9am', 'style': 'width: 100px;'}))
    Friday_end = forms.CharField(required=False, label="To", widget=forms.TextInput(attrs={'placeholder': '5pm', 'style': 'width: 100px;'}))

    Saturday_active = forms.BooleanField(required=False, label="Saturday")
    Saturday_start = forms.CharField(required=False, label="From", widget=forms.TextInput(attrs={'placeholder': '9am', 'style': 'width: 100px;'}))
    Saturday_end = forms.CharField(required=False, label="To", widget=forms.TextInput(attrs={'placeholder': '5pm', 'style': 'width: 100px;'}))

    Sunday_active = forms.BooleanField(required=False, label="Sunday")
    Sunday_start = forms.CharField(required=False, label="From", widget=forms.TextInput(attrs={'placeholder': '9am', 'style': 'width: 100px;'}))
    Sunday_end = forms.CharField(required=False, label="To", widget=forms.TextInput(attrs={'placeholder': '5pm', 'style': 'width: 100px;'}))

    class Meta:
        model = Business
        fields = '__all__'
        widgets = {
            'business_hours': forms.HiddenInput(),
            'ui_theme_color': forms.TextInput(attrs={'type': 'color', 'style': 'height: 40px; width: 60px; padding: 0; cursor: pointer; border: none;'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Load existing business hours if they exist
        business_hours = self.instance.business_hours if (self.instance and self.instance.pk) else {}
        
        # Ensure it's a dict
        if isinstance(business_hours, str):
            try:
                business_hours = json.loads(business_hours)
            except json.JSONDecodeError:
                business_hours = {}
        
        if not isinstance(business_hours, dict):
            business_hours = {}

        # Populate initial values
        for day in DAYS_OF_WEEK:
            if day in business_hours:
                self.fields[f'{day}_active'].initial = True
                times = business_hours[day].split('-')
                if len(times) == 2:
                    self.fields[f'{day}_start'].initial = times[0].strip()
                    self.fields[f'{day}_end'].initial = times[1].strip()

    def clean(self):
        cleaned_data = super().clean()
        new_business_hours = {}

        for day in DAYS_OF_WEEK:
            is_active = cleaned_data.get(f'{day}_active')
            start_time = cleaned_data.get(f'{day}_start')
            end_time = cleaned_data.get(f'{day}_end')

            if is_active:
                if not start_time or not end_time:
                    self.add_error(f'{day}_start', f"Please provide both start and end times for {day}.")
                else:
                    new_business_hours[day] = f"{start_time}-{end_time}"

        cleaned_data['business_hours'] = new_business_hours
        return cleaned_data
