from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='inv_index'),
    path('identifier/<int:pk>', views.identifier_detail, name='identifier-detail'),
]
