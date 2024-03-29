# users/forms.py
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import CustomUser

class CustomUserCreationForm(UserCreationForm):

    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ('username', 'email')
        # fields = UserCreationForm.Meta.fields + ('custom_field',)


class CustomUserChangeForm(UserChangeForm):

    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ('username', 'email')
