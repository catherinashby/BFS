from datetime import datetime

from django.contrib.auth import get_user_model
from django.contrib.auth.forms import (_unicode_ci_compare, AuthenticationForm,
                                       PasswordResetForm, UserCreationForm,
                                       UsernameField)
from django.core.exceptions import ValidationError
from django.forms import CharField, HiddenInput, ModelForm

from .models import User, UserProfile

UserModel = get_user_model()


class CustomUserCreationForm(UserCreationForm):

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        # kludge to get past unique constraint of email address:
        # number of seconds since Day One, converted to hexstring
        interval = (datetime.now() - datetime(1, 1, 1)).total_seconds()
        user.email = hex(int(interval))[2:]
        user.is_active = True
        if commit:
            user.save()
        return user


class UserForm(ModelForm):

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']


class ProfileForm(ModelForm):

    class Meta:
        model = UserProfile
        exclude = ['user']


class UserNameForm(UserForm):

    pressed = CharField(widget=HiddenInput())

    class Meta(UserForm.Meta):
        fields = ['username', 'pressed']

    def clean(self):
        data = self.cleaned_data
        #
        btn = data['pressed'] if 'pressed' in data else '-'
        err_str = {
            'L': 'Name not found -- did you want to register?',
            'R': 'Already in use -- try another username.',
        }
        if 'username' in data:
            if not self.username_found and btn == 'L':
                self._update_errors(ValidationError(err_str[btn]))
            if self.username_found and btn == 'R':
                self._update_errors(ValidationError(err_str[btn]))
        return data

    def clean_pressed(self):
        """
        Convert the value passed in to a codeletter (so we can change the
        button-labels to something else without breaking the view)
        """
        data = self.cleaned_data['pressed']
        if (data == 'login'):
            return 'L'
        if (data == 'register'):
            return 'R'
        self._update_errors(ValidationError('Unknown action received'))
        return '-'

    def clean_username(self):
        """
        Check to see if the selected username is already in use
        """
        data = self.cleaned_data['username']
        lookup_kwargs = {}
        lookup_kwargs['username'] = data
        mc = self.instance.__class__
        qs = mc._default_manager.filter(**lookup_kwargs)
        self.username_found = qs.exists()
        return data


class EmailForm(PasswordResetForm):

    usrname = CharField(widget=HiddenInput())

    def clean(self):
        """
        This is where the new user is saved to the database.
        """
        if not self.errors:
            newUser = UserModel()   # instantiate
            newUser.set_unusable_password()
            newUser.username = self.cleaned_data['usrname']
            for attr, value in self.cleaned_data.items():
                setattr(newUser, attr, value)
            newUser.save()
        return self.cleaned_data

    def clean_email(self):
        """
        Make sure that the email is not on file for any current user.
        """
        data = self.cleaned_data['email']
        email_field_name = UserModel.get_email_field_name()

        dupl_addrs = UserModel._default_manager.filter(**{
            '%s__iexact' % email_field_name: data,
            'is_active': True,
        }).count()
        if dupl_addrs > 0:
            self.add_error('%s' % email_field_name,
                           ValidationError('Email in use -- try another'))

        return data

    def get_users(self, email):
        """Given an email, return matching user(s) who should receive a link
            for registration.
        """
        email_field_name = UserModel.get_email_field_name()
        inactive_users = UserModel._default_manager.filter(**{
            '%s__iexact' % email_field_name: email,
            'is_active': False,
        })
        return (
            u for u in inactive_users
            if not u.has_usable_password() and
            _unicode_ci_compare(email, getattr(u, email_field_name))
        )


class IngressForm(AuthenticationForm):

    username = UsernameField(widget=HiddenInput())

    def get_invalid_login_error(self):
        return ValidationError(
            'Please enter a correct password.',
            code='invalid_login',
            params={'username': self.username_field.verbose_name},
        )
