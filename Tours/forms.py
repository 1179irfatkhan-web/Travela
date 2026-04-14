from django import forms
from .models import UserRegistration
import re


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserRegistration
        fields = ['name', 'email', 'phone', 'city', 'state', 'aadhar_number', 'profile_photo']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your full name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter your email'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your phone number'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your city'}),
            'state': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your state'}),
            'aadhar_number': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'Enter 12-digit Aadhar number', 'maxlength': '12'}),
            'profile_photo': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }

    def clean_aadhar_number(self):
        aadhar = self.cleaned_data.get('aadhar_number')
        if aadhar:
            # Remove any spaces or hyphens
            aadhar = re.sub(r'[\s\-]', '', aadhar)

            # Check if it's exactly 12 digits
            if not aadhar.isdigit() or len(aadhar) != 12:
                raise forms.ValidationError("Aadhar number must be exactly 12 digits")

            # Check if it's unique (excluding current user)
            if UserRegistration.objects.exclude(id=self.instance.id).filter(aadhar_number=aadhar).exists():
                raise forms.ValidationError("This Aadhar number is already registered")

            return aadhar
        return aadhar

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone:
            # Remove any non-digit characters
            phone = re.sub(r'\D', '', phone)
            if len(phone) != 10:
                raise forms.ValidationError("Phone number must be 10 digits")
        return phone

    def clean_profile_photo(self):
        photo = self.cleaned_data.get('profile_photo')
        if photo:
            # Check file size (max 2MB)
            if photo.size > 2 * 1024 * 1024:
                raise forms.ValidationError("Profile photo size should be less than 2MB")

            # Check file extension
            import os
            ext = os.path.splitext(photo.name)[1].lower()
            if ext not in ['.jpg', '.jpeg', '.png', '.gif']:
                raise forms.ValidationError("Only JPG, JPEG, PNG & GIF files are allowed")

        return photo