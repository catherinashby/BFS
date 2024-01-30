from django.urls import path
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required

from . import apis, views

urlpatterns = [
    path('', views.index, name='inv_index'),
    path('shelves', views.shelves, name='shelves'),
    path('suppliers', views.suppliers, name='suppliers'),
    path('itemTemplates', views.itemTemplates, name='itemTemplates'),
    path('images', views.images, name='images'),
    path('identifier/<int:pk>', views.identifier_detail, name='identifier-detail'),
    path('images/upload', views.images_upload, name='images-upload'),

    path('stock', views.stockbook, name='stockBook'),
    path('purchase', login_required(TemplateView.as_view(
                                    template_name="inventory/purchasing.html")), name='purchasing'),

    path('dev', TemplateView.as_view(template_name="inventory/dev.html"), name="dev-api"),
    path('api/locid', apis.LocIdResource.as_list(), name='locid-list'),
    path('api/locid/<int:pk>', apis.LocIdResource.as_detail(), name='locid-detail'),
    path('api/idents/<str:digitstring>', apis.IdentResource.as_detail(), name='ident-detail'),
    path('api/location', apis.LocationResource.as_list(), name='location-list'),
    path('api/location/<int:pk>', apis.LocationResource.as_detail(), name='location-detail'),
    path('api/supplier', apis.SupplierResource.as_list(), name='supplier-list'),
    path('api/supplier/<int:pk>', apis.SupplierResource.as_detail(), name='supplier-detail'),
    path('api/item', apis.ItemTemplateResource.as_list(), name='item-list'),
    path('api/item/<int:pk>', apis.ItemTemplateResource.as_detail(), name='item-detail'),
    path('api/itemdata/<str:digitstring>', apis.ItemDataResource.as_detail(),
         name='itemdata-detail'),
    path('api/itemdata', apis.ItemDataResource.as_list(), name='itemdata-list'),
    path('api/picture', apis.PictureResource.as_list(), name='picture-list'),
    path('api/picture/<int:pk>', apis.PictureResource.as_detail(), name='picture-detail'),
    path('api/stock', apis.StockBookResource.as_list(), name='stock-list'),
    path('api/stock/<int:pk>', apis.StockBookResource.as_detail(), name='stock-detail'),
    path('api/price', apis.PriceResource.as_list(), name='price-list'),
    path('api/price/<int:pk>', apis.PriceResource.as_detail(), name='price-detail'),
    path('api/invoice', apis.InvoiceResource.as_list(), name='invoice-list'),
    path('api/invoice/<int:pk>', apis.InvoiceResource.as_detail(), name='invoice-detail'),
    path('api/purchase', apis.PurchaseResource.as_list(), name='purchase-list'),
    path('api/purchase/<int:pk>', apis.PurchaseResource.as_detail(), name='purchase-detail'),
    path('api/receipt', apis.ReceiptResource.as_list(), name='receipt-list'),
    path('api/receipt/<int:pk>', apis.ReceiptResource.as_detail(), name='receipt-detail'),
    path('api/itemsale', apis.ItemSaleResource.as_list(), name='itemsale-list'),
    path('api/itemsale/<int:pk>', apis.ItemSaleResource.as_detail(), name='itemsale-detail'),
]
