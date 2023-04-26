from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from datetime import date
from typing import Optional


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name=_('user'))
    age = models.DateField(blank=True, null=True, verbose_name=_('date of birth'))
    bio = models.CharField(max_length=100, blank=True, verbose_name=_('bio'))
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True, verbose_name=_('your photo'))

    class Meta:
        verbose_name_plural = _('profiles')
        verbose_name = _('profile')

    def get_age(self) -> Optional[date]:
        if self.age:
            today = date.today()
            birthdate = self.age

            age = today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))
            return age



