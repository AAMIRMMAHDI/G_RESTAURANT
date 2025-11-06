from django import forms


class OrderForm(forms.Form):
    table_number = forms.CharField(
        max_length=10,
        label='شماره میز',
        widget=forms.TextInput(attrs={
            'placeholder': 'مثلاً: 5',
            'class': 'form-control',
            'required': 'required'
        })
    )
    special_requests = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 3,
            'placeholder': 'درخواست خاص (اختیاری)...',
            'class': 'form-control'
        }),
        required=False,
        label='توضیحات'
    )