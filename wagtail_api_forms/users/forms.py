# users/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.utils.translation import gettext_lazy as _
from wagtail.admin.forms.auth import LoginForm
from .models import CustomUser


class EmailOrUsernameLoginForm(LoginForm):
    """Wagtail admin login form for LDAP: accepts email or username."""

    def __init__(self, request=None, *args, **kwargs):
        super().__init__(request, *args, **kwargs)
        self.fields["username"].label = _("Email or username")
        self.fields["username"].widget.attrs["placeholder"] = _(
            "Enter your email or username"
        )

    def get_invalid_login_error(self):
        return forms.ValidationError(
            _("Your email/username and password didn't match. Please try again."),
            code="invalid_login",
        )

class CustomUserCreationForm(UserCreationForm):

    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ('username', 'email')
        # fields = UserCreationForm.Meta.fields + ('custom_field',)


class CustomUserChangeForm(UserChangeForm):

    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ('username', 'email')
