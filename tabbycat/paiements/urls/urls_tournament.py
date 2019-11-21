from django.urls import path

from .. import views

urlpatterns = [
    path('',
        views.PublicPaymentInstitutionView.as_view(),
        name='paiements-tournament-institution'),

    path('add/<int:institution_id>',
        views.PublicPaymentSelectView.as_view(),
        name='paiements-tournament-add'),
]
