# from django.contrib import admin
# from .models import Profile


# @admin.register(Profile)
# class ProfileAdmin(admin.ModelAdmin):

#     list_display = (
#         'user',
#         'role',
#         'phone',
#         'organization',
#         'created_at',
#     )

#     list_filter = (
#         'role',
#         'created_at',
#     )

#     search_fields = (
#         'user__username',
#         'user__first_name',
#         'user__last_name',
#         'phone',
#         'organization',
#     )

#     readonly_fields = (
#         'created_at',
#         'updated_at',
#     )


from django.contrib import admin

from .models import (
    Instrument,
    InstrumentType,
    Profile,
    VerificationApplication,
    VerificationRecord,
    VerificationFile,
    VerificationCertificate,
)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):

    list_display = (
        'user',
        'role',
        'phone',
        'organization',
        'created_at',
    )

    list_filter = (
        'role',
        'created_at',
    )

    search_fields = (
        'user__username',
        'user__first_name',
        'user__last_name',
        'phone',
        'organization',
    )

    readonly_fields = (
        'created_at',
        'updated_at',
    )


@admin.register(InstrumentType)
class InstrumentTypeAdmin(admin.ModelAdmin):

    list_display = (
        'name',
        'is_active',
        'created_at',
    )

    list_filter = (
        'is_active',
    )

    search_fields = (
        'name',
        'description',
    )


@admin.register(Instrument)
class InstrumentAdmin(admin.ModelAdmin):

    list_display = (
        'instrument_id',
        'instrument_type',
        'owner',
        'manufacturer',
        'status',
        'next_due_date',
    )

    list_filter = (
        'status',
        'instrument_type',
        'created_at',
    )

    search_fields = (
        'instrument_id',
        'manufacturer',
        'model_number',
        'serial_number',
        'owner__username',
    )

    readonly_fields = (
        'created_at',
        'updated_at',
    )

    date_hierarchy = 'created_at'


@admin.register(VerificationApplication)
class VerificationApplicationAdmin(admin.ModelAdmin):

    list_display = (
        'application_number',
        'instrument',
        'verification_type',
        'status',
        'assigned_lmo',
        'assigned_gatc',
        'scheduled_date',
        'scheduled_time',
        'application_date',
    )

    list_filter = (
        'status',
        'verification_type',
        'scheduled_date',
        'application_date',
    )

    search_fields = (
        'application_number',
        'instrument__instrument_id',
        'instrument__serial_number',
        'instrument__manufacturer',
        'instrument__model_number',
        'instrument__owner__username',
        'assigned_lmo__username',
        'assigned_gatc__username',
    )

    readonly_fields = (
        'application_number',
        'application_date',
        'created_at',
        'updated_at',
    )

    autocomplete_fields = (
        'instrument',
        'assigned_lmo',
        'assigned_gatc',
    )

    list_per_page = 25

    ordering = (
        '-application_date',
    )



@admin.register(VerificationRecord)
class VerificationRecordAdmin(admin.ModelAdmin):

    list_display = (
        'application',
        'verified_by',
        'result',
        'inspection_date',
        'latitude',
        'longitude',
    )

    list_filter = (
        'result',
        'instrument_condition',
        'inspection_date',
    )

    search_fields = (
        'application__application_number',
        'application__instrument__instrument_id',
        'application__instrument__serial_number',
        'verified_by__username',
    )


@admin.register(VerificationFile)
class VerificationFileAdmin(admin.ModelAdmin):

    list_display = (
        'verification',
        'file_type',
        'description',
        'uploaded_at',
    )

    list_filter = (
        'file_type',
        'uploaded_at',
    )

    search_fields = (
        'verification__application__application_number',
    )


@admin.register(VerificationCertificate)
class VerificationCertificateAdmin(admin.ModelAdmin):

    list_display = (
        'certificate_number',
        'verification',
        'issue_date',
        'valid_until',
        'certificate_status',
    )

    list_filter = (
        'certificate_status',
        'issue_date',
        'valid_until',
    )

    search_fields = (
        'certificate_number',
        'verification__application__application_number',
        'verification__application__instrument__instrument_id',
    )

    readonly_fields = (
        'certificate_number',
        'verification_token',
        'qr_image',
        'created_at',
    )