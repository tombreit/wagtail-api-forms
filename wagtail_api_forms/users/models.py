# users/models.py
from django.contrib.auth.models import AbstractUser


class CustomUser(AbstractUser):

    def clean(self):
        super().clean()

        # Ensure superusers are also staff users:
        if self.is_superuser:
            self.is_staff = True

        # Can this user access the django admin site?
        # if self.groups.filter(name__in=settings.STAFF_GROUPS).exists():
        #     # print("is in groups of '{}'".format(settings.STAFF_GROUPS))
        #     self.is_staff = True

    def __str__(self):
        return self.username
