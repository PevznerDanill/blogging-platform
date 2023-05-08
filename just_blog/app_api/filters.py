from django_filters import rest_framework as filters
from app_auth.models import Profile
from app_blog.models import Post, Blog


class ProfileFilter(filters.FilterSet):
    """
        A filter for the ProfileListApiView (model Profile).
        Allows to filter the list by the date of birth of the profile's owner,
        his username, firstname, lastname and email.

    """
    birthday = filters.DateFromToRangeFilter(field_name='age')
    username = filters.CharFilter(field_name='user__username')
    first_name = filters.CharFilter(field_name='user__first_name')
    last_name = filters.CharFilter(field_name='user__last_name')
    email = filters.CharFilter(field_name='user__email')

    class Meta:
        model = Profile
        fields = 'username', 'first_name', 'last_name', 'email', 'birthday',


class PostFilter(filters.FilterSet):
    """
        A filter for the PostListApiView (model Post).
        Allows to filter the list by username of the post's owner
        (taken from the User instance of the Profile instance),
        its tag, title.
    """
    username = filters.CharFilter(field_name='profile__user__username')
    tag = filters.CharFilter(field_name='tag')
    title = filters.CharFilter(field_name='title')

    class Meta:
        model = Post
        fields = 'username', 'tag', 'title',


class BlogFilter(filters.FilterSet):
    """
        A filter for the BlogListApiView (model Blog).
        Allows to filter the list by the username of the owner of the blog
        (taken from the User instance of the Profile instance),
        and the title of the blog.
    """
    username = filters.CharFilter(field_name='profile__user__username')
    title = filters.CharFilter(field_name='title')

    class Meta:
        model = Blog
        fields = 'username', 'title',

