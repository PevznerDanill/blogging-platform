from app_auth.models import Profile
from django.shortcuts import get_object_or_404
from django.http import HttpRequest


def get_profile_for_context(request: HttpRequest):
    return get_object_or_404(Profile.objects.select_related('user'), user=request.user)
