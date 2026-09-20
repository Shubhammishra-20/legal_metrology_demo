from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
import uuid

class Profile(models.Model):

    ROLE_CHOICES = [
        ('OWNER', 'Instrument Owner'),
        ('LMO', 'Legal Metrology Officer'),
        ('GATC', 'Government Approved Testing Centre'),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile'
    )

    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES
    )

    phone = models.CharField(
        max_length=15,
        blank=True
    )

    organization = models.CharField(
        max_length=200,
        blank=True
    )

    address = models.TextField(
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"


from django.contrib.auth.models import User
from django.db import models


class Profile(models.Model):

    ROLE_CHOICES = [
        ('OWNER', 'Instrument Owner'),
        ('LMO', 'Legal Metrology Officer'),
        ('GATC', 'Government Approved Testing Centre'),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile'
    )

    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES
    )

    phone = models.CharField(
        max_length=15,
        blank=True
    )

    organization = models.CharField(
        max_length=200,
        blank=True
    )

    address = models.TextField(
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"


class InstrumentType(models.Model):

    name = models.CharField(
        max_length=150,
        unique=True
    )

    description = models.TextField(
        blank=True
    )

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.name


class Instrument(models.Model):

    STATUS_CHOICES = [
        ('PENDING', 'Verification Pending'),
        ('VALID', 'Valid'),
        ('EXPIRING', 'Expiring Soon'),
        ('EXPIRED', 'Expired'),
        ('REJECTED', 'Rejected'),
    ]

    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='instruments'
    )

    instrument_type = models.ForeignKey(
        InstrumentType,
        on_delete=models.PROTECT,
        related_name='instruments'
    )

    instrument_id = models.CharField(
        max_length=100,
        unique=True
    )

    manufacturer = models.CharField(
        max_length=150
    )

    model_number = models.CharField(
        max_length=150,
        blank=True
    )

    serial_number = models.CharField(
        max_length=150,
        blank=True
    )

    capacity = models.CharField(
        max_length=100,
        blank=True
    )

    accuracy_class = models.CharField(
        max_length=100,
        blank=True
    )

    location = models.CharField(
        max_length=255
    )

    installation_date = models.DateField(
        null=True,
        blank=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING'
    )

    last_verified_date = models.DateField(
        null=True,
        blank=True
    )

    next_due_date = models.DateField(
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:

        ordering = [
            '-created_at'
        ]

        indexes = [
            models.Index(
                fields=['instrument_id']
            ),
            models.Index(
                fields=['status']
            ),
            models.Index(
                fields=['owner']
            ),
            models.Index(
                fields=['next_due_date']
            ),
        ]

    def __str__(self):
        return f"{self.instrument_id} - {self.instrument_type.name}"


class VerificationApplication(models.Model):

    VERIFICATION_TYPE_CHOICES = [
        ('INITIAL', 'Initial Verification'),
        ('REVERIFICATION', 'Re-Verification'),
    ]

    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('SCHEDULED', 'Scheduled'),
        ('IN_PROGRESS', 'In Progress'),
        ('VERIFIED', 'Verified'),
        ('REJECTED', 'Rejected'),
    ]

    application_number = models.CharField(
        max_length=20,
        unique=True,
        editable=False
    )

    instrument = models.ForeignKey(
        Instrument,
        on_delete=models.CASCADE,
        related_name='verification_applications'
    )

    verification_type = models.CharField(
        max_length=20,
        choices=VERIFICATION_TYPE_CHOICES
    )

    application_date = models.DateTimeField(
        auto_now_add=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING'
    )

    # LMO/GATC assignment
    assigned_lmo = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_lmo_applications'
    )

    assigned_gatc = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_gatc_applications'
    )

    # Verification scheduling
    scheduled_date = models.DateField(
        null=True,
        blank=True
    )

    scheduled_time = models.TimeField(
        null=True,
        blank=True
    )

    assignment_remarks = models.TextField(
        blank=True
    )

    remarks = models.TextField(
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:

        ordering = ['-created_at']

        indexes = [
            models.Index(
                fields=['application_number']
            ),
            models.Index(
                fields=['status']
            ),
            models.Index(
                fields=['application_date']
            ),
            models.Index(
                fields=['assigned_lmo']
            ),
            models.Index(
                fields=['assigned_gatc']
            ),
            models.Index(
                fields=['scheduled_date']
            ),
        ]

    def save(self, *args, **kwargs):

        if not self.application_number:

            import uuid

            self.application_number = (
                f"EMA-{uuid.uuid4().hex[:10].upper()}"
            )

        super().save(*args, **kwargs)

    def __str__(self):

        return self.application_number

class VerificationRecord(models.Model):

    RESULT_CHOICES = [
        ('PASS', 'Verified / Pass'),
        ('FAIL', 'Failed'),
    ]

    CONDITION_CHOICES = [
        ('GOOD', 'Good'),
        ('FAIR', 'Fair'),
        ('POOR', 'Poor'),
        ('DAMAGED', 'Damaged'),
    ]

    application = models.OneToOneField(
        VerificationApplication,
        on_delete=models.CASCADE,
        related_name='verification_record'
    )

    verified_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='verification_records'
    )

    inspection_date = models.DateTimeField(
        default=timezone.now
    )

    result = models.CharField(
        max_length=10,
        choices=RESULT_CHOICES
    )

    instrument_condition = models.CharField(
        max_length=20,
        choices=CONDITION_CHOICES
    )

    observation = models.TextField()

    measurement_details = models.TextField(
        blank=True
    )

    capacity_verified = models.CharField(
        max_length=100,
        blank=True
    )

    accuracy_observed = models.CharField(
        max_length=100,
        blank=True
    )

    seal_condition = models.CharField(
        max_length=255,
        blank=True
    )

    remarks = models.TextField(
        blank=True
    )

    latitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        null=True,
        blank=True
    )

    longitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        null=True,
        blank=True
    )

    location_accuracy = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )

    location_address = models.CharField(
        max_length=500,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return f"{self.application.application_number} - {self.result}"


class VerificationFile(models.Model):

    FILE_TYPE_CHOICES = [
        ('PHOTO', 'Inspection Photo'),
        ('DOCUMENT', 'Supporting Document'),
        ('OTHER', 'Other'),
    ]

    verification = models.ForeignKey(
        VerificationRecord,
        on_delete=models.CASCADE,
        related_name='files'
    )

    file = models.FileField(
        upload_to='verification_files/%Y/%m/'
    )

    file_type = models.CharField(
        max_length=20,
        choices=FILE_TYPE_CHOICES,
        default='PHOTO'
    )

    description = models.CharField(
        max_length=255,
        blank=True
    )

    uploaded_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.file.name


class VerificationCertificate(models.Model):

    verification = models.OneToOneField(
        VerificationRecord,
        on_delete=models.CASCADE,
        related_name='certificate'
    )

    certificate_number = models.CharField(
        max_length=50,
        unique=True
    )

    verification_token = models.CharField(
        max_length=80,
        unique=True,
        default=uuid.uuid4,
        editable=False
    )

    issue_date = models.DateField(
        default=timezone.localdate
    )

    valid_from = models.DateField(
        default=timezone.localdate
    )

    valid_until = models.DateField()

    certificate_status = models.CharField(
        max_length=20,
        default='VALID'
    )

    qr_image = models.ImageField(
        upload_to='certificates/qr/',
        blank=True,
        null=True
    )

    pdf_file = models.FileField(
        upload_to='certificates/pdf/',
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.certificate_number