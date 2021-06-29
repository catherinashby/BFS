from django.conf import settings
from django.urls import path
from django.views.generic import TemplateView

from . import views


urlpatterns = [
    path('signup/', views.SignUpView.as_view(), name='signup'),
    path('access/', views.SigninView.as_view(), name='access'),

    path('entrance/', views.UserNameView.as_view(), name='entrance'),
    path('atrium/', views.EmailAddrView.as_view(), name='atrium'),
    path('narthex/',
         TemplateView.as_view(template_name="accounts/narthex.html"),
         name='narthex'),
    path('vestibule/<uidb64>/<token>/',
         views.RegisterConfirmView.as_view(),
         name='vestibule'),
    path('threshold/',
         TemplateView.as_view(template_name="accounts/threshold.html"),
         name='threshold'),
    path('ingress/', views.PasswordView.as_view(), name='ingress'),

    path('profile/', views.ProfileView.as_view(), name='profile')
]
#
level = getattr(settings, 'LOG_IN_PAGE', 'entrance')
for uP in urlpatterns:  # pragma: no cover
    if uP.name == level:
        log_in = path('log_in/', uP.callback, name="log_in")
        urlpatterns.append(log_in)
        break
