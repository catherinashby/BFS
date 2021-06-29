from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):

    email = models.EmailField(
        'email address',
        unique=True,
        blank=True
    )
    is_active = models.BooleanField(
        'active',
        default=False,
        help_text=(
            'Designates whether this user should be treated as active. '
            'Unselect this instead of deleting accounts.'
        ),
    )


class UserProfile(models.Model):

    class Gender(models.IntegerChoices):
        FEMALE = 1, 'Female'
        MALE = 2, 'Male'
        NONB = 3, 'Non-binary'
        DECLINE = 4, 'Decline to state'

    user = models.OneToOneField(User, on_delete=models.CASCADE,
                                primary_key=True)
    gender = models.IntegerField(choices=Gender.choices,
                                 default=Gender.DECLINE, blank=True)
    location = models.CharField(max_length=100, null=True, blank=True)
    website = models.CharField(max_length=100, null=True, blank=True)
    company = models.CharField(max_length=100, null=True, blank=True)
    about_me = models.TextField(null=True, blank=True)

    def __str__(self):
        return 'Profile for {}'.format(self.user.get_username())
