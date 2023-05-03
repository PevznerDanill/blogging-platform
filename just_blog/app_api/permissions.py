from rest_framework.permissions import BasePermission, SAFE_METHODS
from django.contrib.auth.models import User
from app_auth.models import Profile
from app_blog.models import Blog


class IsUserOrReadOnly(BasePermission):

    def has_object_permission(self, request, view, obj):

        if request.method in SAFE_METHODS:
            return True

        return obj == request.user


class IsBlogsOwner(BasePermission):

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True

        if request.is_authenticated:
            cur_profile = Profile.objects.get(user=request.user)

            return obj.profile == cur_profile


class IsPostOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS and obj.is_published:
            return True
        if request.user.is_authenticated:
            cur_profile = Profile.objects.get(user=request.user)
            return obj.profile == cur_profile


class IsImageOwner(BasePermission):
    def has_object_permission(self, request, view, obj):

        if request.method in SAFE_METHODS:
            return True
        if request.user.is_authenticated:
            cur_profile = Profile.objects.get(user=request.user)
            return obj.post.profile == cur_profile

