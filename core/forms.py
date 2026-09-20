from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.db import transaction
from .models import Profile
from .models import Instrument
from .models import VerificationApplication
from .models import VerificationRecord


class LoginForm(forms.Form):

    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(
            attrs={
                'placeholder': 'Enter username',
                'autocomplete': 'username',
            }
        )
    )

    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                'placeholder': 'Enter password',
                'autocomplete': 'current-password',
            }
        )
    )

    def clean(self):
        cleaned_data = super().clean()

        username = cleaned_data.get('username')
        password = cleaned_data.get('password')

        if username and password:

            user = authenticate(
                username=username,
                password=password
            )

            if user is None:
                raise forms.ValidationError(
                    'Invalid username or password.'
                )

            if not user.is_active:
                raise forms.ValidationError(
                    'This account has been disabled.'
                )

            cleaned_data['user'] = user

        return cleaned_data






class OwnerRegistrationForm(forms.Form):

    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(
            attrs={
                'placeholder': 'Choose a username',
                'autocomplete': 'username',
            }
        )
    )

    first_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(
            attrs={
                'placeholder': 'Enter your first name',
            }
        )
    )

    last_name = forms.CharField(
        max_length=150,
        required=False,
        widget=forms.TextInput(
            attrs={
                'placeholder': 'Enter your last name',
            }
        )
    )

    email = forms.EmailField(
        widget=forms.EmailInput(
            attrs={
                'placeholder': 'Enter email address',
                'autocomplete': 'email',
            }
        )
    )

    phone = forms.CharField(
        max_length=15,
        widget=forms.TextInput(
            attrs={
                'placeholder': 'Enter phone number',
            }
        )
    )

    organization = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(
            attrs={
                'placeholder': 'Business / organization name',
            }
        )
    )

    address = forms.CharField(
        widget=forms.Textarea(
            attrs={
                'placeholder': 'Enter complete address',
                'rows': 3,
            }
        )
    )

    password = forms.CharField(
        min_length=8,
        widget=forms.PasswordInput(
            attrs={
                'placeholder': 'Create password',
                'autocomplete': 'new-password',
            }
        )
    )

    confirm_password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                'placeholder': 'Confirm password',
                'autocomplete': 'new-password',
            }
        )
    )

    def clean_username(self):

        username = self.cleaned_data['username']

        if User.objects.filter(username=username).exists():
            raise forms.ValidationError(
                'This username is already taken.'
            )

        return username

    def clean_email(self):

        email = self.cleaned_data['email']

        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(
                'An account with this email already exists.'
            )

        return email

    def clean_phone(self):

        phone = self.cleaned_data['phone'].strip()

        if not phone.isdigit():
            raise forms.ValidationError(
                'Phone number must contain only digits.'
            )

        if len(phone) < 10 or len(phone) > 15:
            raise forms.ValidationError(
                'Enter a valid phone number.'
            )

        return phone

    def clean(self):

        cleaned_data = super().clean()

        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password:

            if password != confirm_password:

                raise forms.ValidationError(
                    'Passwords do not match.'
                )

        return cleaned_data

    @transaction.atomic
    def create_owner(self):

        user = User.objects.create_user(
            username=self.cleaned_data['username'],
            email=self.cleaned_data['email'],
            password=self.cleaned_data['password'],
            first_name=self.cleaned_data['first_name'],
            last_name=self.cleaned_data['last_name'],
        )

        Profile.objects.create(
            user=user,
            role='OWNER',
            phone=self.cleaned_data['phone'],
            organization=self.cleaned_data['organization'],
            address=self.cleaned_data['address'],
        )

        return user





class InstrumentForm(forms.ModelForm):

    class Meta:

        model = Instrument

        fields = [
            'instrument_type',
            'instrument_id',
            'manufacturer',
            'model_number',
            'serial_number',
            'capacity',
            'accuracy_class',
            'location',
            'installation_date',
        ]

        widgets = {

            'instrument_type': forms.Select(
                attrs={
                    'class': 'form-control'
                }
            ),

            'instrument_id': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Example: INS-2026-0001'
                }
            ),

            'manufacturer': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Manufacturer name'
                }
            ),

            'model_number': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Model number'
                }
            ),

            'serial_number': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Serial number'
                }
            ),

            'capacity': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Example: 100 kg'
                }
            ),

            'accuracy_class': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Example: Class III'
                }
            ),

            'location': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Installation/location address'
                }
            ),

            'installation_date': forms.DateInput(
                attrs={
                    'class': 'form-control',
                    'type': 'date'
                }
            ),
        }

    def clean_instrument_id(self):

        instrument_id = self.cleaned_data['instrument_id'].strip()

        if Instrument.objects.filter(
            instrument_id=instrument_id
        ).exists():

            raise forms.ValidationError(
                'This Instrument ID is already registered.'
            )

        return instrument_id





class VerificationApplicationForm(forms.ModelForm):
    class Meta:
        model = VerificationApplication
        fields = [
            'instrument',
            'verification_type',
            'remarks',
        ]

        widgets = {
            'instrument': forms.Select(attrs={
                'class': 'form-control',
            }),

            'verification_type': forms.Select(attrs={
                'class': 'form-control',
            }),

            'remarks': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Enter any additional information (optional)',
            }),
        }

    def __init__(self, *args, owner=None, **kwargs):
        super().__init__(*args, **kwargs)

        if owner:
            self.fields['instrument'].queryset = (
                Instrument.objects.filter(
                    owner=owner
                ).order_by('instrument_id')
            )




class LMOApplicationAssignmentForm(forms.ModelForm):

    class Meta:
        model = VerificationApplication

        fields = [
            'assigned_lmo',
            'assigned_gatc',
            'scheduled_date',
            'scheduled_time',
            'assignment_remarks',
            'status',
        ]

        widgets = {

            'assigned_lmo': forms.Select(
                attrs={
                    'class': 'form-control'
                }
            ),

            'assigned_gatc': forms.Select(
                attrs={
                    'class': 'form-control'
                }
            ),

            'scheduled_date': forms.DateInput(
                attrs={
                    'class': 'form-control',
                    'type': 'date'
                }
            ),

            'scheduled_time': forms.TimeInput(
                attrs={
                    'class': 'form-control',
                    'type': 'time'
                }
            ),

            'assignment_remarks': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 4,
                    'placeholder': 'Enter assignment instructions or remarks...'
                }
            ),

            'status': forms.Select(
                attrs={
                    'class': 'form-control'
                }
            ),
        }

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        # Only LMO users
        self.fields['assigned_lmo'].queryset = (
            User.objects
            .filter(profile__role='LMO')
            .order_by('username')
        )

        # Only GATC users
        self.fields['assigned_gatc'].queryset = (
            User.objects
            .filter(profile__role='GATC')
            .order_by('username')
        )

        # LMO can only use these statuses
        self.fields['status'].choices = [
            ('PENDING', 'Pending'),
            ('SCHEDULED', 'Scheduled'),
        ]



class GATCVerificationForm(forms.ModelForm):

    class Meta:
        model = VerificationRecord

        fields = [
            'result',
            'instrument_condition',
            'observation',
            'measurement_details',
            'capacity_verified',
            'accuracy_observed',
            'seal_condition',
            'remarks',
            'latitude',
            'longitude',
            'location_accuracy',
            'location_address',
        ]

        widgets = {

            'result': forms.Select(
                attrs={'class': 'form-control'}
            ),

            'instrument_condition': forms.Select(
                attrs={'class': 'form-control'}
            ),

            'observation': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 4,
                    'placeholder': 'Enter inspection observations...'
                }
            ),

            'measurement_details': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 4,
                    'placeholder': 'Enter measurement/test readings...'
                }
            ),

            'capacity_verified': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Example: 30 kg'
                }
            ),

            'accuracy_observed': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Enter observed accuracy'
                }
            ),

            'seal_condition': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Seal condition / seal number'
                }
            ),

            'remarks': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 3,
                    'placeholder': 'Additional remarks'
                }
            ),

            'latitude': forms.HiddenInput(),

            'longitude': forms.HiddenInput(),

            'location_accuracy': forms.HiddenInput(),

            'location_address': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'readonly': 'readonly',
                    'placeholder': 'Current location will appear here'
                }
            ),
        }