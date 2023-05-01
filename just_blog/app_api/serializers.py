from rest_framework import serializers
from app_auth.models import Profile
from django.contrib.auth.models import User
from app_blog.models import Blog, Post, Image


class CurrentProfileDefault:
    requires_context = True

    def __call__(self, serializer_field):
        cur_profile = Profile.objects.get(user=serializer_field.context['request'].user)
        return cur_profile

    def __repr__(self):
        return '%s()' % self.__class__.__name__


class ProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = 'bio', 'age', 'avatar'


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = 'id', 'username', 'first_name', 'last_name', 'email', 'profile'
        extra_kwargs = {'username': {'read_only': True}}

    profile = ProfileUpdateSerializer()

    def update(self, instance, validated_data):
        cur_profile = instance.profile
        profile_data = validated_data.pop('profile')
        for key, value in profile_data.items():
            setattr(cur_profile, key, value)
        cur_profile.save()
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()
        return instance


class ProfileShortSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Profile
        fields = 'id', 'username',


class BlogShortSerializer(serializers.ModelSerializer):

    class Meta:
        model = Blog
        fields = 'id', 'title'


class ProfileSerializer(serializers.ModelSerializer):
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

    class Meta:
        model = Blog
        fields = 'id', 'title', 'description', 'profile',
        extra_kwargs = {'id': {'read_only': True}}

    profile = serializers.HiddenField(default=CurrentProfileDefault())


class ImageShortSerializer(serializers.ModelSerializer):

    class Meta:
        model = Image
        fields = 'id', 'title'


class PostSerializer(serializers.ModelSerializer):

    class Meta:
        model = Post
        fields = 'id', 'title', 'tag', 'content', 'created_at', 'is_published', 'blog', 'profile', 'images'

    blog = BlogShortSerializer()
    profile = ProfileShortSerializer()
    images = ImageShortSerializer(many=True, read_only=True)


class ImageCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Image
        fields = 'image',


class CreateUserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = 'username', 'password',
        extra_kwargs = {'password': {'write_only': True}}


class BlogDetailSerializer(serializers.ModelSerializer):

    class Meta:
        model = Blog
        fields = 'id', 'title', 'description', 'posts', 'profile',

    posts = serializers.HyperlinkedRelatedField(
        many=True,
        read_only=True,
        view_name='app_blog:post_detail'
    )

    profile = ProfileShortSerializer(read_only=True)


class PostCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Post
        fields = (
            'id', 'title', 'tag', 'blog', 'profile',
            'content',
        )
        extra_kwargs = {'id': {'read_only': True}}

    profile = serializers.HiddenField(default=CurrentProfileDefault())

    def __init__(self, *args, **kwargs):
        context = kwargs.get('context')
        profile = context.get('profile')
        super().__init__(*args, **kwargs)
        self.fields['blog'] = serializers.PrimaryKeyRelatedField(
            queryset=Blog.objects.filter(profile=profile)
        )


class PostDetailSerializer(serializers.ModelSerializer):

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
        }

    images = ImageShortSerializer(many=True, read_only=True)


class ImageCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Image
        fields = (
            'id', 'title', 'image', 'post',
        )
        extra_kwargs = {'id': {'read_only': True}}

    def __init__(self, *args, **kwargs):
        context = kwargs.get('context')
        profile = context.get('profile')
        super().__init__(*args, **kwargs)
        self.fields['post'] = serializers.PrimaryKeyRelatedField(
            queryset=Post.objects.filter(profile=profile)
        )


class ImageDetailSerializer(serializers.ModelSerializer):

    class Meta:
        model = Image
        fields = (
            'id', 'title', 'image', 'post',
        )
        extra_kwargs = {'id': {'read_only': True}, 'post': {'read_only': True}}
