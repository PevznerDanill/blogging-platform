from rest_framework.permissions import BasePermission, SAFE_METHODS
from django.contrib.auth.models import User
from app_auth.models import Profile
from app_blog.models import Blog


class IsUserOrReadOnly(BasePermission):

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in SAFE_METHODS:
            return True

        # Instance must have an attribute named `owner`.
        return obj == request.user


class IsBlogsOwner(BasePermission):

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in SAFE_METHODS:
            return True

        # Instance must have an attribute named `owner`.
        if request.is_authenticated:
            cur_profile = Profile.objects.get(user=request.user)

            return obj.profile == cur_profile


class IsPostOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.

        if request.method in SAFE_METHODS and obj.is_published:
            return True
        if request.user.is_authenticated:
            cur_profile = Profile.objects.get(user=request.user)
            return obj.profile == cur_profile


class IsImageOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.

        if request.method in SAFE_METHODS:
            return True
        if request.user.is_authenticated:
            cur_profile = Profile.objects.get(user=request.user)
            return obj.post.profile == cur_profile

