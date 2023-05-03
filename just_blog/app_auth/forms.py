from django.contrib.auth import password_validation
from django.contrib.auth.forms import UserChangeForm, AuthenticationForm, UsernameField, UserCreationForm
from django.contrib.auth.models import User
from django import forms
from .models import Profile
from datetime import date
from django.utils.translation import gettext_lazy as _


class MyUserCreationForm(UserCreationForm):
    password1 = forms.CharField(
        label=_("Password"),
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password", 'class': 'input'}),
        help_text=password_validation.password_validators_help_text_html(),
    )
    password2 = forms.CharField(
        label=_("Password confirmation"),
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password", 'class': 'input'}),
        strip=False,
        help_text=_("Enter the same password as before, for verification."),
    )

    username = forms.CharField(
        max_length=150,
        help_text=_(
            "Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only."
        ),
        widget=forms.TextInput(attrs={'class': 'input'}),
        error_messages={
            "unique": _("A user with that username already exists."),
        },
        label=_('User name')
    )


class MyUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = 'first_name', 'last_name', 'email',

    first_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'input'}),
        label=_('First name')
    )

    last_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'input'}),
        label=_('Last name')
    )

    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'input email-input'}),
        label=_('Email')
    )

    password = None


class MyLoginForm(AuthenticationForm):
    username = UsernameField(
        widget=forms.TextInput(attrs={"autofocus": True, 'class': 'input'}),
        label=_('User name')
    )
    password = forms.CharField(
        label=_("Password"),
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "current-password", 'class': 'input'}),
    )


class ProfileForm(forms.ModelForm):

    class Meta:
        model = Profile
        fields = 'age', 'bio', 'avatar',

    bio = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'input', 'cols': '50', 'rows': '5'},),
        required=False,
        label=_('Bio')
    )

    age = forms.DateField(
        widget=forms.SelectDateWidget(years=range(1902, 2018), attrs={'class': 'input age-input'}),
        required=False,
        label=_('Age')
    )

    avatar = forms.ImageField(
        label=_('Avatar'),
        required=False,
        widget=forms.ClearableFileInput(attrs={'class': 'image_input'})
    )
