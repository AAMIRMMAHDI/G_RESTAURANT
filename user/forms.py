from django import forms
from .models import User


class MobileForm(forms.Form):
    mobile = forms.CharField(
        max_length=15,
        label='شماره موبایل',
        widget=forms.TextInput(attrs={'placeholder': '09123456789'})
    )


class OTPForm(forms.Form):
    code = forms.CharField(
        max_length=4,
        label='کد تأیید',
        widget=forms.TextInput(attrs={'placeholder': '1234'})
    )


class UserRegistrationForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name']
        widgets = {
            'first_name': forms.TextInput(attrs={'placeholder': 'نام'}),
            'last_name': forms.TextInput(attrs={'placeholder': 'نام خانوادگی'}),
        }


class UserManagementForm(forms.ModelForm):
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'national_code', 'mobile',
            'email', 'birth_date', 'hire_date', 'role', 'status', 'address'
        ]
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
            'hire_date': forms.DateInput(attrs={'type': 'date'}),
            'address': forms.Textarea(attrs={'rows': 3}),
        }