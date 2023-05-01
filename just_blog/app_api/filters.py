from django_filters import rest_framework as filters
from app_auth.models import Profile
from app_blog.models import Post, Blog


class ProfileFilter(filters.FilterSet):
    birthday = filters.DateFromToRangeFilter(field_name='age')
    username = filters.CharFilter(field_name='user__username')
    first_name = filters.CharFilter(field_name='user__first_name')
    last_name = filters.CharFilter(field_name='user__last_name')
    email = filters.CharFilter(field_name='user__email')

    class Meta:
        model = Profile
        fields = 'username', 'first_name', 'last_name', 'email', 'birthday',


class PostFilter(filters.FilterSet):
    username = filters.CharFilter(field_name='profile__user__username')
    tag = filters.CharFilter(field_name='tag')
    title = filters.CharFilter(field_name='title')
    is_published = filters.BooleanFilter(field_name='is_published')

    class Meta:
        model = Post
        fields = 'username', 'tag', 'title', 'is_published',


class BlogFilter(filters.FilterSet):
    username = filters.CharFilter(field_name='profile__user__username')
    title = filters.CharFilter(field_name='title')

    class Meta:
        model = Blog
        fields = 'username', 'title',

