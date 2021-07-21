from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='inv_index'),
    path('identifier/<int:pk>', views.identifier_detail, name='identifier-detail'),

    path('api/locid', views.LocIdResource.as_list(), name='locid-list'),
    path('api/locid/<int:pk>', views.LocIdResource.as_detail(), name='locid-detail'),
]
