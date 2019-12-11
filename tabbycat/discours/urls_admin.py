from django.urls import include, path

from . import views

urlpatterns = [

    path('',
        views.DiscoursIndexView.as_view(),
        name='discours-index'),

    path('<int:round_seq>/', include([
        path('draw/',
            views.DiscoursDrawView.as_view(),
            name='discours-draw'),
        path('create/',
            views.DiscoursCreateRoundView.as_view(),
            name='discours-create'),
        path('results/<int:salle_id>',
            views.DiscoursResultsView.as_view(),
            name='discours-saisie'),
    ])),
]
