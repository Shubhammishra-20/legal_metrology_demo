from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render, get_object_or_404
from .forms import (
    InstrumentForm,
    LoginForm,
    OwnerRegistrationForm,
    VerificationApplication,
)
from .models import (
    Profile,
    InstrumentType,
    Instrument,
    VerificationApplication,
    VerificationRecord,
    VerificationFile,
    VerificationCertificate,
)
from django.db.models import Q
from .forms import VerificationApplicationForm
from .forms import LMOApplicationAssignmentForm
from django.utils import timezone
from django.conf import settings
import os
import uuid
import qrcode
from .forms import GATCVerificationForm
from datetime import timedelta
from django.core.files import File
from django.http import FileResponse, HttpResponse
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from io import BytesIO
from django.core.files.base import ContentFile


def home(request):
    return render(request, 'home.html')


def login_view(request):

    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':

        form = LoginForm(request.POST)

        if form.is_valid():

            user = form.cleaned_data['user']

            login(request, user)

            return redirect('dashboard')

    else:
        form = LoginForm()

    return render(
        request,
        'login.html',
        {
            'form': form
        }
    )


@login_required
def logout_view(request):

    logout(request)

    messages.success(
        request,
        'You have been logged out successfully.'
    )

    return redirect('login')


@login_required
def dashboard(request):

    if request.user.is_superuser:

        return render(
            request,
            'dashboard.html',
            {
                'role': 'ADMIN'
            }
        )

    try:
        profile = request.user.profile

    except Exception:

        logout(request)

        messages.error(
            request,
            'Your account profile is not configured.'
        )

        return redirect('login')

    # LMO → LMO Dashboard
    if profile.role == 'LMO':
        return redirect('lmo_dashboard')
    
    if profile.role == 'GATC':
        return redirect('gatc_dashboard')

    # OWNER → Normal Dashboard
    if profile.role == 'OWNER':
        return render(
            request,
            'dashboard.html',
            {
                'role': profile.role,
                'profile': profile,
            }
        )

    # GATC → temporary normal dashboard
    if profile.role == 'GATC':
        return render(
            request,
            'dashboard.html',
            {
                'role': profile.role,
                'profile': profile,
            }
        )

    return redirect('dashboard')

def register_view(request):

    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':

        form = OwnerRegistrationForm(request.POST)

        if form.is_valid():

            user = form.create_owner()

            login(request, user)

            messages.success(
                request,
                'Your owner account has been created successfully.'
            )

            return redirect('dashboard')

    else:

        form = OwnerRegistrationForm()

    return render(
        request,
        'register.html',
        {
            'form': form
        }
    )



@login_required
def my_instruments(request):

    if request.user.is_superuser:
        return redirect('/admin/')

    try:
        profile = request.user.profile
    except Exception:

        messages.error(
            request,
            'Your account profile is not configured.'
        )

        return redirect('dashboard')

    if profile.role != 'OWNER':

        messages.error(
            request,
            'You do not have permission to access instruments.'
        )

        return redirect('dashboard')

    instruments = Instrument.objects.filter(
        owner=request.user
    ).select_related(
        'instrument_type'
    )

    search = request.GET.get(
        'search',
        ''
    ).strip()

    status = request.GET.get(
        'status',
        ''
    ).strip()

    if search:

        instruments = instruments.filter(
            Q(instrument_id__icontains=search)
            |
            Q(manufacturer__icontains=search)
            |
            Q(model_number__icontains=search)
            |
            Q(serial_number__icontains=search)
        )

    if status:

        instruments = instruments.filter(
            status=status
        )

    return render(
        request,
        'instruments.html',
        {
            'instruments': instruments,
            'search': search,
            'selected_status': status,
            'status_choices': Instrument.STATUS_CHOICES,
        }
    )




@login_required
def add_instrument(request):

    if request.user.is_superuser:
        return redirect('/admin/')

    try:
        profile = request.user.profile
    except Exception:

        messages.error(
            request,
            'Your account profile is not configured.'
        )

        return redirect('dashboard')

    if profile.role != 'OWNER':

        messages.error(
            request,
            'Only instrument owners can register instruments.'
        )

        return redirect('dashboard')

    if request.method == 'POST':

        form = InstrumentForm(request.POST)

        if form.is_valid():

            instrument = form.save(
                commit=False
            )

            instrument.owner = request.user

            instrument.status = 'PENDING'

            instrument.save()

            messages.success(
                request,
                'Instrument registered successfully.'
            )

            return redirect(
                'my_instruments'
            )

    else:

        form = InstrumentForm()

    return render(
        request,
        'form.html',
        {
            'form': form,
            'title': 'Register Instrument',
            'button_text': 'Register Instrument',
        }
    )


@login_required
def apply_verification(request):
    if not hasattr(request.user, 'profile'):
        return redirect('dashboard')

    if request.user.profile.role != 'OWNER':
        return redirect('dashboard')

    if request.method == 'POST':
        form = VerificationApplicationForm(
            request.POST,
            owner=request.user
        )

        if form.is_valid():
            application = form.save(commit=False)

            # Extra security check
            if application.instrument.owner != request.user:
                messages.error(
                    request,
                    'You can only apply for your own instruments.'
                )
                return redirect('apply_verification')

            application.save()

            messages.success(
                request,
                f'Application submitted successfully. '
                f'Application No: {application.application_number}'
            )

            return redirect('verification_applications')

    else:
        form = VerificationApplicationForm(
            owner=request.user
        )

    return render(
        request,
        'verification_form.html',
        {
            'form': form,
        }
    )



@login_required
def verification_applications(request):

    profile = get_object_or_404(
        Profile,
        user=request.user
    )

    if profile.role != 'OWNER':

        messages.error(
            request,
            'Only instrument owners can access this page.'
        )

        return redirect('dashboard')


    applications = (
        VerificationApplication.objects
        .filter(
            instrument__owner=request.user
        )
        .select_related(
            'instrument',
            'instrument__instrument_type'
        )
        .prefetch_related(
            'verification_record__certificate'
        )
        .order_by('-created_at')
    )


    return render(
        request,
        'verification_applications.html',
        {
            'applications': applications
        }
    )



@login_required
def lmo_dashboard(request):
    # Only LMO can access this dashboard
    if not hasattr(request.user, 'profile'):
        return redirect('dashboard')

    if request.user.profile.role != 'LMO':
        return redirect('dashboard')

    total_applications = VerificationApplication.objects.count()

    pending_applications = VerificationApplication.objects.filter(
        status='PENDING'
    ).count()

    scheduled_applications = VerificationApplication.objects.filter(
        status='SCHEDULED'
    ).count()

    in_progress_applications = VerificationApplication.objects.filter(
        status='IN_PROGRESS'
    ).count()

    verified_applications = VerificationApplication.objects.filter(
        status='VERIFIED'
    ).count()

    rejected_applications = VerificationApplication.objects.filter(
        status='REJECTED'
    ).count()

    recent_applications = (
        VerificationApplication.objects
        .select_related(
            'instrument',
            'instrument__owner',
            'instrument__instrument_type'
        )
        .order_by('-application_date')[:10]
    )

    context = {
        'total_applications': total_applications,
        'pending_applications': pending_applications,
        'scheduled_applications': scheduled_applications,
        'in_progress_applications': in_progress_applications,
        'verified_applications': verified_applications,
        'rejected_applications': rejected_applications,
        'recent_applications': recent_applications,
    }

    return render(
        request,
        'lmo_dashboard.html',
        context
    )

@login_required
def gatc_dashboard(request):

    # Only GATC can access this dashboard
    if not hasattr(request.user, 'profile'):
        return redirect('dashboard')

    if request.user.profile.role != 'GATC':
        return redirect('dashboard')

    total_applications = VerificationApplication.objects.count()

    pending_applications = VerificationApplication.objects.filter(
        status='PENDING'
    ).count()

    scheduled_applications = VerificationApplication.objects.filter(
        status='SCHEDULED'
    ).count()

    in_progress_applications = VerificationApplication.objects.filter(
        status='IN_PROGRESS'
    ).count()

    verified_applications = VerificationApplication.objects.filter(
        status='VERIFIED'
    ).count()

    rejected_applications = VerificationApplication.objects.filter(
        status='REJECTED'
    ).count()

    recent_applications = (
        VerificationApplication.objects
        .select_related(
            'instrument',
            'instrument__owner',
            'instrument__instrument_type'
        )
        .order_by('-application_date')[:10]
    )

    context = {
        'total_applications': total_applications,
        'pending_applications': pending_applications,
        'scheduled_applications': scheduled_applications,
        'in_progress_applications': in_progress_applications,
        'verified_applications': verified_applications,
        'rejected_applications': rejected_applications,
        'recent_applications': recent_applications,
    }

    return render(
        request,
        'gatc_dashboard.html',
        context
    )


@login_required
def review_application(request, application_id):

    # Only LMO can review applications
    if not hasattr(request.user, 'profile'):
        return redirect('dashboard')

    if request.user.profile.role != 'LMO':
        messages.error(
            request,
            'Only Legal Metrology Officers can review applications.'
        )
        return redirect('dashboard')

    application = get_object_or_404(
        VerificationApplication.objects.select_related(
            'instrument',
            'instrument__owner',
            'instrument__instrument_type'
        ),
        id=application_id
    )

    if request.method == 'POST':

        form = LMOApplicationAssignmentForm(
            request.POST,
            instance=application
        )

        if form.is_valid():

            updated_application = form.save(
                commit=False
            )

            updated_application.save()

            messages.success(
                request,
                f'Application {application.application_number} '
                f'has been updated successfully.'
            )

            return redirect(
                'lmo_dashboard'
            )

    else:

        form = LMOApplicationAssignmentForm(
            instance=application
        )

    return render(
        request,
        'lmo_review_application.html',
        {
            'application': application,
            'form': form,
        }
    )


@login_required
def gatc_assigned_applications(request):

    if not hasattr(request.user, 'profile'):
        return redirect('dashboard')

    if request.user.profile.role != 'GATC':
        messages.error(
            request,
            'Only Government Approved Testing Centres can access this page.'
        )
        return redirect('dashboard')

    applications = (
        VerificationApplication.objects
        .filter(assigned_gatc=request.user)
        .select_related(
            'instrument',
            'instrument__owner',
            'instrument__instrument_type'
        )
        .order_by('-scheduled_date', '-created_at')
    )

    return render(
        request,
        'gatc_assigned_applications.html',
        {
            'applications': applications
        }
    )


@login_required
def start_verification(request, application_id):

    # Only GATC can perform verification
    if not hasattr(request.user, 'profile'):
        return redirect('dashboard')

    if request.user.profile.role != 'GATC':
        messages.error(
            request,
            'Only GATC can perform verification.'
        )
        return redirect('dashboard')

    # Only assigned application can be opened
    application = get_object_or_404(
        VerificationApplication.objects.select_related(
            'instrument',
            'instrument__owner',
            'instrument__instrument_type'
        ),
        id=application_id,
        assigned_gatc=request.user
    )

    # Application must be scheduled/in progress
    if application.status not in ['SCHEDULED', 'IN_PROGRESS']:
        messages.error(
            request,
            'This application is not available for field verification.'
        )
        return redirect('gatc_assigned_applications')

    # Get existing verification record if available
    verification = getattr(
        application,
        'verification_record',
        None
    )

    # ------------------------------------------------
    # POST
    # ------------------------------------------------

    if request.method == 'POST':

        form = GATCVerificationForm(
            request.POST,
            instance=verification
        )

        photos = request.FILES.getlist('photos')
        documents = request.FILES.getlist('documents')

        # DEBUG / VALIDATION
        if not form.is_valid():

            messages.error(
                request,
                'Please correct the errors shown below.'
            )

            return render(
                request,
                'gatc_verification.html',
                {
                    'application': application,
                    'form': form,
                    'verification': verification,
                }
            )

        # --------------------------------------------
        # SAVE VERIFICATION RECORD
        # --------------------------------------------

        record = form.save(commit=False)

        record.application = application
        record.verified_by = request.user
        record.inspection_date = timezone.now()

        record.save()

        # --------------------------------------------
        # SAVE PHOTOS
        # --------------------------------------------

        for photo in photos:

            VerificationFile.objects.create(
                verification=record,
                file=photo,
                file_type='PHOTO',
                description='GATC inspection photograph'
            )

        # --------------------------------------------
        # SAVE DOCUMENTS
        # --------------------------------------------

        for document in documents:

            VerificationFile.objects.create(
                verification=record,
                file=document,
                file_type='DOCUMENT',
                description='Supporting verification document'
            )

        # --------------------------------------------
        # PASS
        # --------------------------------------------

        if record.result == 'PASS':

            today = timezone.localdate()

            # Valid for 1 year
            valid_until = today + timedelta(days=365)

            # Update application
            application.status = 'VERIFIED'
            application.save(
                update_fields=['status', 'updated_at']
            )

            # Update instrument
            instrument = application.instrument

            instrument.status = 'VALID'
            instrument.last_verified_date = today
            instrument.next_due_date = valid_until

            instrument.save(
                update_fields=[
                    'status',
                    'last_verified_date',
                    'next_due_date'
                ]
            )

            # ----------------------------------------
            # GENERATE CERTIFICATE
            # ----------------------------------------

            certificate = create_verification_certificate(
                record,
                valid_until
            )

            messages.success(
                request,
                'Verification completed successfully. '
                f'Certificate {certificate.certificate_number} '
                'has been generated.'
            )

            return redirect(
                'certificate_detail',
                certificate_id=certificate.id
            )

        # --------------------------------------------
        # FAIL
        # --------------------------------------------

        else:

            application.status = 'REJECTED'
            application.save(
                update_fields=['status', 'updated_at']
            )

            instrument = application.instrument
            instrument.status = 'REJECTED'

            instrument.save(
                update_fields=['status']
            )

            messages.warning(
                request,
                'Verification failed. '
                'The application has been rejected.'
            )

            return redirect(
                'gatc_assigned_applications'
            )

    # ------------------------------------------------
    # GET
    # ------------------------------------------------

    else:

        if verification:

            form = GATCVerificationForm(
                instance=verification
            )

        else:

            form = GATCVerificationForm()

    return render(
        request,
        'gatc_verification.html',
        {
            'application': application,
            'form': form,
            'verification': verification,
        }
    )


def create_verification_certificate(
    verification,
    valid_until
):

    today = timezone.localdate()

    certificate_number = (
        'CERT-'
        + str(today.year)
        + '-'
        + uuid.uuid4().hex[:8].upper()
    )

    # --------------------------------------------
    # CREATE CERTIFICATE
    # --------------------------------------------

    certificate = VerificationCertificate.objects.create(
        verification=verification,
        certificate_number=certificate_number,
        issue_date=today,
        valid_from=today,
        valid_until=valid_until,
        certificate_status='VALID'
    )

    qr_data = request.build_absolute_uri(
        f"/certificate/verify/{certificate.verification_token}/"
    )

    qr = qrcode.make(qr_data)

    buffer = BytesIO()
    qr.save(buffer, format="PNG")

    certificate.qr_image.save(
        f"{certificate.certificate_number}.png",
        ContentFile(buffer.getvalue()),
        save=True
    )
    # --------------------------------------------
    # QR URL
    # --------------------------------------------

    verification_url = (
        settings.SITE_URL
        + '/verify/'
        + certificate.verification_token
        + '/'
    )

    # --------------------------------------------
    # GENERATE QR
    # --------------------------------------------

    qr = qrcode.make(
        verification_url
    )

    qr_directory = os.path.join(
        settings.MEDIA_ROOT,
        'certificates',
        'qr'
    )

    os.makedirs(
        qr_directory,
        exist_ok=True
    )

    qr_filename = (
        certificate.verification_token
        + '.png'
    )

    qr_path = os.path.join(
        qr_directory,
        qr_filename
    )

    qr.save(qr_path)

    certificate.qr_image = (
        'certificates/qr/'
        + qr_filename
    )

    certificate.save(
        update_fields=['qr_image']
    )

    # --------------------------------------------
    # PDF
    # --------------------------------------------

    pdf_directory = os.path.join(
        settings.MEDIA_ROOT,
        'certificates',
        'pdf'
    )

    os.makedirs(
        pdf_directory,
        exist_ok=True
    )

    pdf_filename = (
        certificate.certificate_number
        + '.pdf'
    )

    pdf_path = os.path.join(
        pdf_directory,
        pdf_filename
    )

    generate_certificate_pdf(
        certificate,
        pdf_path
    )

    # Save PDF into Django FileField
    with open(
        pdf_path,
        'rb'
    ) as pdf_file:

        certificate.pdf_file.save(
            pdf_filename,
            File(pdf_file),
            save=True
        )

    return certificate

def generate_certificate_pdf(
    certificate,
    pdf_path
):

    verification = certificate.verification

    application = verification.application

    instrument = application.instrument

    owner = instrument.owner

    instrument_type = instrument.instrument_type

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'CertificateTitle',
        parent=styles['Title'],
        fontSize=20,
        leading=25,
        alignment=1,
        textColor=colors.HexColor('#065f46'),
        spaceAfter=8
    )

    subtitle_style = ParagraphStyle(
        'CertificateSubtitle',
        parent=styles['Normal'],
        fontSize=11,
        leading=15,
        alignment=1,
        textColor=colors.HexColor('#374151'),
        spaceAfter=15
    )

    normal_style = ParagraphStyle(
        'NormalCertificate',
        parent=styles['Normal'],
        fontSize=9.5,
        leading=14
    )

    heading_style = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading3'],
        fontSize=12,
        textColor=colors.HexColor('#065f46'),
        spaceBefore=12,
        spaceAfter=8
    )

    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm
    )

    elements = []

    # =====================================
    # HEADER
    # =====================================

    elements.append(
        Paragraph(
            'e-Maapan',
            title_style
        )
    )

    elements.append(
        Paragraph(
            'DIGITAL VERIFICATION CERTIFICATE',
            subtitle_style
        )
    )

    elements.append(
        Paragraph(
            'Online Verification System for Weighing '
            'and Measuring Instruments',
            subtitle_style
        )
    )

    elements.append(
        Spacer(1, 5)
    )

    # =====================================
    # VERIFIED STATUS
    # =====================================

    status_table = Table(
        [
            [
                Paragraph(
                    '<b>✓ INSTRUMENT VERIFIED</b>',
                    normal_style
                )
            ]
        ],
        colWidths=[170 * mm]
    )

    status_table.setStyle(
        TableStyle([
            (
                'BACKGROUND',
                (0, 0),
                (-1, -1),
                colors.HexColor('#dcfce7')
            ),
            (
                'TEXTCOLOR',
                (0, 0),
                (-1, -1),
                colors.HexColor('#166534')
            ),
            (
                'ALIGN',
                (0, 0),
                (-1, -1),
                'CENTER'
            ),
            (
                'BOX',
                (0, 0),
                (-1, -1),
                0.8,
                colors.HexColor('#86efac')
            ),
            (
                'TOPPADDING',
                (0, 0),
                (-1, -1),
                10
            ),
            (
                'BOTTOMPADDING',
                (0, 0),
                (-1, -1),
                10
            ),
        ])
    )

    elements.append(status_table)

    # =====================================
    # CERTIFICATE DETAILS
    # =====================================

    elements.append(
        Paragraph(
            'Certificate Information',
            heading_style
        )
    )

    certificate_data = [
        [
            'Certificate Number',
            certificate.certificate_number
        ],
        [
            'Issue Date',
            str(certificate.issue_date)
        ],
        [
            'Valid From',
            str(certificate.valid_from)
        ],
        [
            'Valid Until',
            str(certificate.valid_until)
        ],
    ]

    certificate_table = Table(
        certificate_data,
        colWidths=[65 * mm, 105 * mm]
    )

    certificate_table.setStyle(
        TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            (
                'BACKGROUND',
                (0, 0),
                (0, -1),
                colors.HexColor('#f0fdf4')
            ),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('PADDING', (0, 0), (-1, -1), 8),
        ])
    )

    elements.append(certificate_table)

    # =====================================
    # INSTRUMENT DETAILS
    # =====================================

    elements.append(
        Paragraph(
            'Instrument Details',
            heading_style
        )
    )

    instrument_data = [
        ['Instrument ID', instrument.instrument_id],
        ['Instrument Type', instrument_type.name],
        ['Manufacturer', instrument.manufacturer],
        ['Model Number', instrument.model_number],
        ['Serial Number', instrument.serial_number],
        ['Capacity', instrument.capacity],
        ['Location', instrument.location],
    ]

    instrument_table = Table(
        instrument_data,
        colWidths=[65 * mm, 105 * mm]
    )

    instrument_table.setStyle(
        TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            (
                'BACKGROUND',
                (0, 0),
                (0, -1),
                colors.HexColor('#f0fdf4')
            ),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('PADDING', (0, 0), (-1, -1), 8),
        ])
    )

    elements.append(instrument_table)

    # =====================================
    # OWNER / VERIFICATION
    # =====================================

    elements.append(
        Paragraph(
            'Verification Information',
            heading_style
        )
    )

    verifier_name = (
        verification.verified_by.get_full_name()
        if verification.verified_by
        else 'GATC Officer'
    )

    verification_data = [
        [
            'Owner',
            owner.get_full_name()
        ],
        [
            'Verified By',
            verifier_name
        ],
        [
            'Inspection Date',
            str(verification.inspection_date)
        ],
        [
            'Verification Result',
            verification.get_result_display()
        ],
        [
            'Instrument Condition',
            verification.get_instrument_condition_display()
        ],
    ]

    verification_table = Table(
        verification_data,
        colWidths=[65 * mm, 105 * mm]
    )

    verification_table.setStyle(
        TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            (
                'BACKGROUND',
                (0, 0),
                (0, -1),
                colors.HexColor('#f0fdf4')
            ),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('PADDING', (0, 0), (-1, -1), 8),
        ])
    )

    elements.append(verification_table)

    # =====================================
    # QR CODE
    # =====================================

    if certificate.qr_image:

        qr_path = certificate.qr_image.path

        if os.path.exists(qr_path):

            elements.append(
                Spacer(1, 15)
            )

            elements.append(
                Paragraph(
                    '<b>Scan QR Code to Verify Certificate</b>',
                    ParagraphStyle(
                        'QRTitle',
                        parent=normal_style,
                        alignment=1,
                        fontSize=11
                    )
                )
            )

            elements.append(
                Spacer(1, 8)
            )

            qr_image = Image(
                qr_path,
                width=38 * mm,
                height=38 * mm
            )

            qr_table = Table(
                [[qr_image]],
                colWidths=[170 * mm]
            )

            qr_table.setStyle(
                TableStyle([
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ])
            )

            elements.append(qr_table)

            elements.append(
                Spacer(1, 8)
            )

            elements.append(
                Paragraph(
                    'This QR code contains only a unique '
                    'verification URL. Certificate details '
                    'are fetched securely from the e-Maapan database.',
                    ParagraphStyle(
                        'QRDescription',
                        parent=normal_style,
                        alignment=1,
                        fontSize=8
                    )
                )
            )

    # =====================================
    # FOOTER
    # =====================================

    elements.append(
        Spacer(1, 20)
    )

    elements.append(
        Paragraph(
            'This is a digitally generated verification '
            'certificate from the e-Maapan system.',
            ParagraphStyle(
                'Footer',
                parent=normal_style,
                alignment=1,
                fontSize=8,
                textColor=colors.grey
            )
        )
    )

    doc.build(elements)

@login_required
def certificate_detail(
    request,
    certificate_id
):

    certificate = get_object_or_404(
        VerificationCertificate.objects.select_related(
            'verification',
            'verification__application',
            'verification__application__instrument',
            'verification__application__instrument__owner',
            'verification__application__instrument__instrument_type',
            'verification__verified_by'
        ),
        id=certificate_id
    )

    instrument = (
        certificate.verification
        .application
        .instrument
    )

    profile = get_object_or_404(
        Profile,
        user=request.user
    )

    # Owner can see own certificate
    # GATC can see certificate
    # LMO can see certificate

    if (
        profile.role == 'OWNER'
        and instrument.owner != request.user
    ):

        messages.error(
            request,
            'You are not authorized to view this certificate.'
        )

        return redirect('dashboard')


    return render(
        request,
        'certificate_detail.html',
        {
            'certificate': certificate,
            'verification': certificate.verification,
            'instrument': instrument,
        }
    )


def public_certificate_verification(
    request,
    verification_token
):

    certificate = get_object_or_404(
        VerificationCertificate.objects.select_related(
            'verification',
            'verification__application',
            'verification__application__instrument',
            'verification__application__instrument__owner',
            'verification__application__instrument__instrument_type',
            'verification__verified_by'
        ),
        verification_token=verification_token
    )


    today = timezone.localdate()

    is_valid = (
        certificate.certificate_status == 'VALID'
        and certificate.valid_until >= today
    )


    return render(
        request,
        'public_certificate_verification.html',
        {
            'certificate': certificate,
            'verification': certificate.verification,
            'instrument':
                certificate.verification.application.instrument,
            'is_valid': is_valid,
        }
    )




@login_required
def download_certificate(request, certificate_id):

    certificate = get_object_or_404(
        VerificationCertificate.objects.select_related(
            'verification',
            'verification__application',
            'verification__application__instrument'
        ),
        id=certificate_id
    )

    instrument = (
        certificate.verification
        .application
        .instrument
    )

    # OWNER can download only his own certificate
    if instrument.owner != request.user:

        messages.error(
            request,
            'You are not authorized to download this certificate.'
        )

        return redirect('dashboard')


    if not certificate.pdf_file:

        messages.error(
            request,
            'Certificate PDF is not available.'
        )

        return redirect(
            'verification_applications'
        )


    response = FileResponse(
        certificate.pdf_file.open('rb'),
        as_attachment=True,
        filename=(
            certificate.certificate_number
            + '.pdf'
        )
    )

    return response