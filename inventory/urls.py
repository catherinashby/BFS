from django.urls import path

from . import views, apis

urlpatterns = [
    path('', views.index, name='inv_index'),
    path('identifier/<int:pk>', apis.identifier_detail, name='identifier-detail'),
]
