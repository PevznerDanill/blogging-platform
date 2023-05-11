from django.contrib.auth import password_validation
from django.contrib.auth.forms import UserChangeForm, AuthenticationForm, UsernameField, UserCreationForm
from django.contrib.auth.models import User
from django import forms
from .models import Profile
from datetime import date
from django.utils.translation import gettext_lazy as _
from django.forms.widgets import ClearableFileInput


class MyInput(ClearableFileInput):
    """
    Overrides the is_initial method of the ClearableFileInput widget
    """
    def is_initial(self, value):
        """
        Always returns False so the widget won't display the messages saved for non-initial value.
        """
        return False


class MyUserCreationForm(UserCreationForm):
    """
    Overrides the UserCreation form, adding classes to the widgets.
    """
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
    """
    Overrides the UserChangeForm, removing password field and adding classes to other widgets.
    """
    class Meta:
        model = User
        fields = 'first_name', 'last_name', 'email',

    first_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'input'}),
        label=_('First name'),
        required=False
    )

    last_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'input'}),
        label=_('Last name'),
        required=False
    )

    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'input email-input'}),
        label=_('Email'),
        required=False
    )

    password = None


class MyLoginForm(AuthenticationForm):
    """
    Overrides the AuthenticationForm, adding classes to the widget.
    """
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
    """
    A form for the model Profile.
    """

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
        label=_('Upload your avatar'),
        required=False,
        widget=MyInput(attrs={'class': 'avatar_input'})
    )
