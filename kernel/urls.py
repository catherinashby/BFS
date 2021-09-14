from django.urls import path
from django.views.generic import TemplateView

urlpatterns = [
    path('', TemplateView.as_view(template_name="qUnit_base.html")),
    path('bb_val', TemplateView.as_view(template_name="testJS/backbone_validation.html")),

]
