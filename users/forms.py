from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import User, Role


class CustomUserCreationForm(forms.ModelForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'vTextField',
            'placeholder': 'Enter email address'
        })
    )
    first_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'vTextField',
            'placeholder': 'Enter first name'
        })
    )
    last_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'vTextField',
            'placeholder': 'Enter last name'
        })
    )
    role = forms.ModelChoiceField(
        queryset=Role.objects.all(),
        required=True,
        empty_label="Select a role",
        widget=forms.Select(attrs={
            'class': 'vSelectField'
        })
    )

    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'role', 'is_active', 'is_staff', 'is_superuser')

    def save(self, commit=True):
        # Don't set a password here; admin's save_model() will handle it
        user = super().save(commit=False)
        if commit:
            user.save()
        return user


class CustomUserChangeForm(UserChangeForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'vTextField',
            'readonly': 'readonly'
        })
    )

    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'role', 'is_active', 'is_staff', 'is_superuser')


class LoginForm(forms.Form):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email address',
            'id': 'email'
        })
    )
    password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your password',
            'id': 'password'
        })
    )


class PasswordResetForm(forms.Form):
    new_password = forms.CharField(
        required=True,
        min_length=8,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter new password'
        })
    )
    confirm_password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm new password'
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')

        if new_password and confirm_password:
            if new_password != confirm_password:
                raise forms.ValidationError("New passwords don't match.")

        return cleaned_data