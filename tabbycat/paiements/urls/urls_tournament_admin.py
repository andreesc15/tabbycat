from django.urls import path

from .. import views

urlpatterns = [
    path('',
        views.AdminPaymentView.as_view(),
        name='paiements-tournament-admin'),

    path('add/',
        views.AdminPaymentSelectView.as_view(),
        name='paiements-tournament-add-admin'),
]
