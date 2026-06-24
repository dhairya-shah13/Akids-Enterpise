from django import forms
from django.contrib.auth import get_user_model
from .models import Address

User = get_user_model()


class RegistrationForm(forms.ModelForm):
    """User registration form with email, name, phone, and password."""

    password = forms.CharField(
        min_length=8,
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Create a password (min 8 chars)',
            'class': 'form-input',
        })
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Confirm your password',
            'class': 'form-input',
        })
    )

    class Meta:
        model = User
        fields = ['email', 'full_name', 'phone']
        widgets = {
            'email': forms.EmailInput(attrs={
                'placeholder': 'you@example.com',
                'class': 'form-input',
            }),
            'full_name': forms.TextInput(attrs={
                'placeholder': 'Your full name',
                'class': 'form-input',
            }),
            'phone': forms.TextInput(attrs={
                'placeholder': 'Phone number (optional)',
                'class': 'form-input',
            }),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email', '').lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm = cleaned_data.get('confirm_password')
        if password and confirm and password != confirm:
            self.add_error('confirm_password', 'Passwords do not match.')
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user


class LoginForm(forms.Form):
    """Email + password login form."""

    email = forms.EmailField(widget=forms.EmailInput(attrs={
        'placeholder': 'you@example.com',
        'class': 'form-input',
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'placeholder': 'Your password',
        'class': 'form-input',
    }))


class ProfileForm(forms.ModelForm):
    """Edit user profile (name and phone)."""

    class Meta:
        model = User
        fields = ['full_name', 'phone']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-input'}),
            'phone': forms.TextInput(attrs={'class': 'form-input'}),
        }


class AddressForm(forms.ModelForm):
    """Add or edit a shipping address."""

    class Meta:
        model = Address
        fields = ['label', 'full_name', 'phone', 'line1', 'line2',
                  'city', 'state', 'pincode', 'is_default']
        widgets = {
            'label': forms.TextInput(attrs={
                'placeholder': 'e.g. Home, Office',
                'class': 'form-input',
            }),
            'full_name': forms.TextInput(attrs={
                'placeholder': 'Recipient name',
                'class': 'form-input',
            }),
            'phone': forms.TextInput(attrs={
                'placeholder': 'Phone number',
                'class': 'form-input',
            }),
            'line1': forms.TextInput(attrs={
                'placeholder': 'Address line 1',
                'class': 'form-input',
            }),
            'line2': forms.TextInput(attrs={
                'placeholder': 'Address line 2 (optional)',
                'class': 'form-input',
            }),
            'city': forms.TextInput(attrs={
                'placeholder': 'City',
                'class': 'form-input',
            }),
            'state': forms.TextInput(attrs={
                'placeholder': 'State',
                'class': 'form-input',
            }),
            'pincode': forms.TextInput(attrs={
                'placeholder': 'Pincode',
                'class': 'form-input',
            }),
            'is_default': forms.CheckboxInput(attrs={
                'class': 'form-checkbox',
            }),
        }
