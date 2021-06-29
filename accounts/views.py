from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import (LoginView, PasswordResetConfirmView,
                                       PasswordResetView)
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import CreateView, FormView

from .forms import (CustomUserCreationForm, EmailForm, IngressForm,
                    ProfileForm, UserForm, UserNameForm)


class SignUpView(CreateView):
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('access')
    template_name = 'accounts/signup.html'


class SigninView(LoginView):
    profile_url = reverse_lazy('profile')
    template_name = 'accounts/access.html'

    def get_success_url(self):
        usr = self.request.user

        firstTimer = True
        if hasattr(usr, 'userprofile'):
            firstTimer = False

        url = self.profile_url if firstTimer else super().get_success_url()
        return url


@method_decorator(login_required, name='dispatch')
class ProfileView(FormView):

    form_class = ProfileForm
    success_url = reverse_lazy('profile')
    template_name = 'accounts/profile.html'

    def get(self, request, *args, **kwargs):
        if request.user.email.find('@') == -1:
            request.user.email = None
        user_form = UserForm(instance=request.user)
        if hasattr(request.user, 'userprofile'):
            profile_form = ProfileForm(instance=request.user.userprofile)
        else:
            gdef = ProfileForm.Meta.model.gender.field.default
            profile_form = ProfileForm({'user': request.user,
                                        'gender': gdef})
        self.extra_context = {'userform': user_form, 'form': profile_form}
        return super().get(request, args, kwargs)

    def post(self, request, *args, **kwargs):
        user_form = UserForm(request.POST, instance=request.user)
        profile_form = self.get_form()
        self.extra_context = {'userform': user_form, 'form': profile_form}
        if user_form.is_valid() and profile_form.is_valid():
            profile_form.instance.user = user_form.save()
            profile_form.save()
            self.extra_context['saved'] = True
        # always return to the profile form
        return self.form_invalid(profile_form)


class UserNameView(View):
    form_class = UserNameForm
    template_name = 'accounts/entrance.html'

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            btn = form.cleaned_data['pressed']
            messages.success(request,
                             form.cleaned_data['username'],
                             extra_tags='username')
            if btn == 'L':
                dest = 'ingress'
            if btn == 'R':
                dest = 'atrium'
            return redirect(dest)

        return render(request, self.template_name, {'form': form})


class EmailAddrView(PasswordResetView):

    email_template_name = 'accounts/registration_email.html'
    extra_email_context = None
    form_class = EmailForm
    from_email = None
    html_email_template_name = None
    subject_template_name = 'accounts/registration_subject.txt'
    success_url = reverse_lazy('narthex')
    template_name = 'accounts/atrium.html'
    title = 'Registration'
    token_generator = default_token_generator

    def get(self, request, *args, **kwargs):
        context = self.get_context_data()

        for msg in messages.get_messages(request):
            if msg.level_tag == 'success':
                if 'username' in msg.tags.split():
                    fm = context['form']
                    fm.initial = {'usrname': msg.message}
                    context['form'] = fm

        return self.render_to_response(context)

    def form_valid(self, form):
        opts = {
            'use_https': self.request.is_secure(),
            'token_generator': self.token_generator,
            'from_email': self.from_email,
            'email_template_name': self.email_template_name,
            'subject_template_name': self.subject_template_name,
            'request': self.request,
            'html_email_template_name': self.html_email_template_name,
            'extra_email_context': self.extra_email_context,
        }
        if hasattr(settings, 'SERVICE_HOSTNAME'):
            opts['domain_override'] = settings.SERVICE_HOSTNAME
        form.save(**opts)
        return super().form_valid(form)


class RegisterConfirmView(PasswordResetConfirmView):
    template_name = 'accounts/vestibule.html'
    success_url = reverse_lazy('threshold')

    def form_valid(self, form):

        form.user.is_active = True
        return super().form_valid(form)


class PasswordView(LoginView):

    form_class = IngressForm
    profile_url = reverse_lazy('profile')
    template_name = 'accounts/ingress.html'

    def get(self, request, *args, **kwargs):
        context = self.get_context_data()

        for msg in messages.get_messages(request):
            if msg.level_tag == 'success':
                if 'username' in msg.tags.split():
                    fm = context['form']
                    fm.initial = {'username': msg.message}
                    context['form'] = fm

        return self.render_to_response(context)

    def get_success_url(self):
        usr = self.request.user

        firstTimer = True
        if hasattr(usr, 'userprofile'):
            firstTimer = False

        url = self.profile_url if firstTimer else super().get_success_url()
        return url
