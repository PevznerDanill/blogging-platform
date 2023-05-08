from app_auth.models import Profile
from django.shortcuts import get_object_or_404
from django.http import HttpRequest, Http404
from typing import Union


def get_profile_for_context(request: HttpRequest) -> Union[Profile, Http404]:
    """
    This method returns the Profile instance getting it from the related User instance
    saved in request.user, if it exists, otherwise raises Http404.
    """
    return get_object_or_404(Profile.objects.select_related('user'), user=request.user)
