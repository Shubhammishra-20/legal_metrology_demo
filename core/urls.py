from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views
from .views import home


urlpatterns = [

    path('', home, name='home'),
    
    path(
        'login/',
        views.login_view,
        name='login'
    ),

    path(
        'register/',
        views.register_view,
        name='register'
    ),

    path(
        'logout/',
        views.logout_view,
        name='logout'
    ),

    path(
        'dashboard/',
        views.dashboard,
        name='dashboard'
    ),

    path(
        'instruments/',
        views.my_instruments,
        name='my_instruments'
    ),

    path(
        'instruments/add/',
        views.add_instrument,
        name='add_instrument'
    ),

    path(
        'verification/apply/',
        views.apply_verification,
        name='apply_verification'
    ),
    
    path(
        'verification/applications/',
        views.verification_applications,
        name='verification_applications'
    ),
    path(
        'lmo/dashboard/',
        views.lmo_dashboard,
        name='lmo_dashboard'
    ),
    path(
        'gatc/dashboard/',
        views.gatc_dashboard,
        name='gatc_dashboard'
    ),
    path(
        'lmo/application/<int:application_id>/review/',
        views.review_application,
        name='review_application'
    ),
    path(
        'gatc/applications/',
        views.gatc_assigned_applications,
        name='gatc_assigned_applications'
    ),

    path(
        'gatc/application/<int:application_id>/verify/',
        views.start_verification,
        name='start_verification'
    ),

    path(
        'certificate/<int:certificate_id>/',
        views.certificate_detail,
        name='certificate_detail'
    ),

    path(
        'verify/<str:verification_token>/',
        views.public_certificate_verification,
        name='public_certificate_verification'
    ),

    path(
        'certificate/<int:certificate_id>/download/',
        views.download_certificate,
        name='download_certificate'
    ),
]

urlpatterns += static(
    settings.MEDIA_URL,
    document_root=settings.MEDIA_ROOT
)