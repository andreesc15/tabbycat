from django.urls import include, path

from .. import views

urlpatterns = [
    path('',
        views.PublicAdhesionPaymentView.as_view(),
        name='paiements-adhesion'),

    path('return/',
        views.PaymentReturnView.as_view(),
        name='paiements-return'),

    path('admin/', include([
        path('',
            views.AdminAdhesionPaymentView.as_view(),
            name='paiements-adhesion-admin'),

        path('update/',
            views.PaymentRefreshView.as_view(),
            name='paiements-refresh'),
    ])),
]
