from rest_framework import serializers
from rest_framework.fields import CurrentUserDefault
from app_auth.models import Profile
from django.contrib.auth.models import User
from app_blog.models import Blog, Post, Image
from typing import Dict, Union


class CurrentProfileDefault(CurrentUserDefault):
    """
        Overrides the CurrentUserDefault field from rest_framework. In the __call__ method
        instead of returning request.user instance gets the related Profile instance and
        returns it.
    """

    def __call__(self, serializer_field):
        cur_profile = Profile.objects.get(user=serializer_field.context['request'].user)
        return cur_profile


class ProfileSerializer(serializers.ModelSerializer):
    """
        A serializer for the Profile model with the fields bio, age and avatar (ergo all except user).
        Used in the UserSerializer for the definition of the field profile.
    """
    class Meta:
        model = Profile
        fields = 'id', 'bio', 'age', 'avatar', 'user',
        extra_kwargs = {'bio': {'required': False}, 'age': {'required': False}}

    user = serializers.HiddenField(default=CurrentUserDefault())
    avatar = serializers.ImageField(required=False)


class ProfileShortSerializer(serializers.ModelSerializer):
    """
        A serializer for the Profile model with the fields id and the field username
        taken from the related User instance.
        Used in PostSerializer and BlogDetailSerializer for the definition of the field profile.
    """
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Profile
        fields = 'id', 'username',


class BlogShortSerializer(serializers.ModelSerializer):
    """
        A serializer for the Blog model with the fields id and title.
        Used in PostSerializer for the definition of the blog field.
    """

    class Meta:
        model = Blog
        fields = 'id', 'title'


class ProfileFullSerializer(serializers.ModelSerializer):
    """
        A serializer for the Profile model. Not only includes all of its fields but also
        the fields of the related User instance.
        The fields blogs and posts are represented as hyper linked related fields.
        Used in the ProfileListApiView.
    """
    username = serializers.CharField(source='user.username', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    blogs = serializers.HyperlinkedRelatedField(
        many=True,
        read_only=True,
        view_name='app_blog:blog_detail'
    )
    posts = serializers.HyperlinkedRelatedField(
        many=True,
        read_only=True,
        view_name='app_blog:post_detail'
    )

    avatar = serializers.ImageField()

    class Meta:
        model = Profile
        fields = 'id', 'user', 'username', 'first_name', 'last_name', 'email', 'age', 'bio', 'avatar', 'blogs', 'posts'


class BlogCreateSerializer(serializers.ModelSerializer):
    """
        A serializer for the Blog model with the fields id, title,
        description and profile, taken as a CurrentProfileDefault hidden field.
        Used in BlogCreateApiView.
    """

    class Meta:
        model = Blog
        fields = 'id', 'title', 'description', 'profile',
        extra_kwargs = {'id': {'read_only': True}}

    profile = serializers.HiddenField(default=CurrentProfileDefault())


class ImageShortSerializer(serializers.ModelSerializer):
    """
        A serializer for the Image model with the fields id and title.
        Used in the PostSerializer and the PostDetailSerializer for the definition
        of the images field.
    """

    class Meta:
        model = Image
        fields = 'id', 'title'


class PostSerializer(serializers.ModelSerializer):
    """
        A serializer for the Post model with all of its fields.
        Used in the PostListApiView.
    """

    class Meta:
        model = Post
        fields = 'id', 'title', 'tag', 'content', 'created_at', 'is_published', 'blog', 'profile', 'images'

    blog = BlogShortSerializer()
    profile = ProfileShortSerializer()
    images = ImageShortSerializer(many=True, read_only=True)


class BlogDetailSerializer(serializers.ModelSerializer):
    """
        A serializer for the Blog model with the field id, title,
        description, posts and profile.
        The field posts is defined as a HyperlinkedRelatedField.
        The field profile is defined with the ProfileShortSerializer.
        Used in the BlogDetailApiView and the BlogListApiView.
    """

    class Meta:
        model = Blog
        fields = 'id', 'title', 'description', 'posts', 'profile',
        extra_kwargs = {
            'id': {'read_only': True},
            'description': {'required': False},
            'title': {'required': False}
        }

    posts = serializers.HyperlinkedRelatedField(
        many=True,
        read_only=True,
        view_name='app_blog:post_detail'
    )

    profile = ProfileShortSerializer(read_only=True)


class PostCreateSerializer(serializers.ModelSerializer):
    """
        A serializer for the Post model with the fields id, title, tag,
        blog, profile and content.
        The profile field is defined as hidden field.
        Used in the PostCreateApiView.
    """

    class Meta:
        model = Post
        fields = (
            'id', 'title', 'tag', 'blog', 'profile',
            'content',
        )
        extra_kwargs = {'id': {'read_only': True}}

    profile = serializers.HiddenField(default=CurrentProfileDefault())

    def __init__(self, *args, **kwargs):
        """
            Overrides the __init__ method to retrieve only the blogs related to the current
            Profile instance.
        """
        context = kwargs.get('context')
        profile = context.get('profile')
        super().__init__(*args, **kwargs)
        self.fields['blog'] = serializers.PrimaryKeyRelatedField(
            queryset=Blog.objects.filter(profile=profile)
        )


class PostDetailSerializer(serializers.ModelSerializer):
    """
        A serializer for the Post model with all its fields.
        The images field is defined with the ImageShortSerializer.
        Used in the PostUpdateApiView.
    """

    class Meta:
        model = Post
        fields = (
            'id', 'title', 'tag', 'blog', 'profile',
            'content', 'created_at', 'is_published', 'published_at', 'images'
        )
        extra_kwargs = {
            'id': {'read_only': True},
            'created_at': {'read_only': True},
            'published_at': {'read_only': True},
            'profile': {'read_only': True},
            'blog': {'read_only': True},
            'title': {'required': False},
            'tag': {'required': False},
            'content': {'required': False},
            'is_published': {'required': False},
        }

    images = ImageShortSerializer(many=True, read_only=True)


class ImageCreateSerializer(serializers.ModelSerializer):
    """
        A serializer for the Image model with the fields id, title, image and post.
        Used in the ImageCreateApiView.
    """

    class Meta:
        model = Image
        fields = (
            'id', 'title', 'image', 'post',
        )
        extra_kwargs = {'id': {'read_only': True}}

    def __init__(self, *args, **kwargs):
        """
            Overrides the __init__ method to retrieve from only the posts
            related to the current Profile instance.
        """
        context = kwargs.get('context')
        profile = context.get('profile')
        super().__init__(*args, **kwargs)
        self.fields['post'] = serializers.PrimaryKeyRelatedField(
            queryset=Post.objects.filter(profile=profile)
        )


class ImageDetailSerializer(serializers.ModelSerializer):
    """
        A serializer for the Image model with all its fields.
    """

    class Meta:
        model = Image
        fields = (
            'id', 'title', 'image', 'post',
        )
        extra_kwargs = {
            'id': {'read_only': True},
            'post': {'read_only': True},
            'image': {'required': False},
            'title': {'required': False},
        }
