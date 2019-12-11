from django.urls import path

from . import views

urlpatterns = [

    path('draw/',
        views.PublicDiscoursDrawView.as_view(),
        name='public-discours-draw'),

    path('<slug:url_key>/',
        views.PrivateurlResultsView.as_view(),
        name='privateurls-discours-results'),
]
