from rest_framework.permissions import BasePermission, SAFE_METHODS
from app_auth.models import Profile
from app_blog.models import Blog, Post, Image
from django.http import HttpRequest
from rest_framework.views import View
from django.contrib.auth.models import User


class IsProfile(BasePermission):
    """
        Checks if the current user already has a related Profile instance
    """

    def has_permission(self, request: HttpRequest, view: View) -> bool:

        return not Profile.objects.filter(user=request.user).exists()


class IsProfileOwnerOrReadOnly(BasePermission):
    """
        Checks if the retrieved Profile instance is the same as the Profile instance related to
        the User instance saved in request.user. If False, only safe methods are allowed
    """

    def has_object_permission(self, request: HttpRequest, view: View, obj: Profile) -> bool:

        if request.method in SAFE_METHODS:
            return True

        return obj.user == request.user


class IsUserOrReadOnly(BasePermission):
    """
        Checks if the retrieved User instance is the same as User instance saved in the request.user.
    """

    def has_object_permission(self, request: HttpRequest, view: View, obj: User) -> bool:

        if request.method in SAFE_METHODS:
            return True

        return obj == request.user


class IsBlogsOwner(BasePermission):
    """
        Checks if the Profile instance related to the request.user is the same as
        the Profile instance related to the retrieved Blog instance.
    """

    def has_object_permission(self, request: HttpRequest, view: View, obj: Blog) -> bool:
        if request.method in SAFE_METHODS:
            return True

        if request.user.is_authenticated:
            cur_profile: Profile = Profile.objects.get(user=request.user)

            return obj.profile == cur_profile


class IsPostOwner(BasePermission):
    """
        Checks if the Profile instance related to the request.user is the same as
        the Profile instance related to the retrieved Post instance.
    """

    def has_object_permission(self, request: HttpRequest, view: View, obj: Post) -> bool:
        if request.method in SAFE_METHODS and obj.is_published:
            return True
        if request.user.is_authenticated:
            cur_profile: Profile = Profile.objects.get(user=request.user)
            return obj.profile == cur_profile


class IsImageOwner(BasePermission):
    """
        Checks if the Profile instance related to the request.user is the same as
        the Profile instance related to the Post instances related to the retrieved Image instance.
        To perform this check there is an annotated field owner (post__profile) added to the queryset
        in the ImageDetailApiView.
    """

    def has_object_permission(self, request: HttpRequest, view: View, obj: Image) -> bool:

        if request.method in SAFE_METHODS:
            return True
        if request.user.is_authenticated:
            cur_profile: Profile = Profile.objects.select_related('user').get(user=request.user)
            return obj.post.profile == cur_profile

