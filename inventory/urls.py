from django.urls import path
from . import apis, views

urlpatterns = [
    path('', views.index, name='inv_index'),
    path('shelves', views.shelves, name='shelves'),
    path('suppliers', views.suppliers, name='suppliers'),
    path('itemTemplates', views.itemTemplates, name='itemTemplates'),
    path('identifier/<int:pk>', views.identifier_detail, name='identifier-detail'),

    path('api/locid', apis.LocIdResource.as_list(), name='locid-list'),
    path('api/locid/<int:pk>', apis.LocIdResource.as_detail(), name='locid-detail'),
    path('api/location', apis.LocationResource.as_list(), name='location-list'),
    path('api/location/<int:pk>', apis.LocationResource.as_detail(), name='location-detail'),
    path('api/supplier', apis.SupplierResource.as_list(), name='supplier-list'),
    path('api/supplier/<int:pk>', apis.SupplierResource.as_detail(), name='supplier-detail'),
    path('api/item', apis.ItemTemplateResource.as_list(), name='item-list'),
    path('api/item/<int:pk>', apis.ItemTemplateResource.as_detail(), name='item-detail'),

]
