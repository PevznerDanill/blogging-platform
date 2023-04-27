from django.contrib.auth.forms import UserChangeForm
from django.contrib.auth.models import User
from django import forms
from .models import Profile
from datetime import date
from django.utils.translation import gettext_lazy as _


class MyUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = 'first_name', 'last_name', 'email',

    password = None


class ProfileForm(forms.ModelForm):

    class Meta:
        model = Profile
        fields = 'age', 'bio', 'avatar',

    bio = forms.CharField(widget=forms.Textarea, required=False, label=_('Bio'))

    age = forms.DateField(widget=forms.SelectDateWidget(
        empty_label=(_('year'), _('month'), _('day')),
        years=range(1902, 2018)
    ), initial=date(year=date.today().year - 5,
                    month=date.today().month,
                    day=date.today().day),
        required=False, label=_('Age'))

    avatar = forms.ImageField(
        label=_('Avatar'),
        required=False,
    )
