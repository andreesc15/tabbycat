from django.urls import include, path

from . import views

urlpatterns = [

    path('draw/',
        views.PublicDiscoursDrawView.as_view(),
        name='public-discours-draw'),

    path('<slug:url_key>/', include([
        path('results/',
            views.PrivateurlResultsView.as_view(),
            name='privateurls-discours-results'),
        path('inscription/',
            views.PrivateurlInscriptionView.as_view(),
            name='privateurls-discours-inscription'),
    ])),
]
