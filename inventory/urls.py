from django.urls import path
from . import apis, views

urlpatterns = [
    path('', views.index, name='inv_index'),
    path('shelves', views.shelves, name='shelves'),
    path('identifier/<int:pk>', views.identifier_detail, name='identifier-detail'),

    path('api/locid', apis.LocIdResource.as_list(), name='locid-list'),
    path('api/locid/<int:pk>', apis.LocIdResource.as_detail(), name='locid-detail'),
    path('api/location', apis.LocationResource.as_list(), name='location-list'),
    path('api/location/<int:pk>', apis.LocationResource.as_detail(), name='location-detail'),

]
