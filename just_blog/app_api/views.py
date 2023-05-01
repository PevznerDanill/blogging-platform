from django.contrib.auth import authenticate, login
from django.shortcuts import render, reverse
from rest_framework.settings import api_settings
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from app_auth.models import Profile
from app_blog.models import Blog, Post, Image
from rest_framework.generics import GenericAPIView, RetrieveUpdateDestroyAPIView, RetrieveDestroyAPIView, CreateAPIView, RetrieveAPIView
from rest_framework.mixins import ListModelMixin, CreateModelMixin, RetrieveModelMixin, DestroyModelMixin, UpdateModelMixin
from .serializers import (
    ProfileSerializer,
    CreateUserSerializer,
    UserSerializer,
    BlogCreateSerializer,
    BlogDetailSerializer,
    PostCreateSerializer,
    PostDetailSerializer,
    ImageCreateSerializer,
    ImageDetailSerializer,
    PostSerializer,
)
from django.http import HttpRequest, HttpResponseRedirect
from rest_framework.response import Response
from .filters import ProfileFilter, PostFilter, BlogFilter
from django.db.models import F
from rest_framework import filters, viewsets, status
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth.models import User
from .permissions import IsUserOrReadOnly, IsBlogsOwner, IsPostOwner, IsImageOwner


class ProfileListApiView(ListModelMixin, GenericAPIView):
    queryset = Profile.objects.select_related('user').prefetch_related('blogs', 'posts').all()
    serializer_class = ProfileSerializer
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = 'user__username', 'user__first_name', 'user__last_name', 'user__email', 'age'
    filterset_class = ProfileFilter

    def get(self, request: HttpRequest) -> Response:
        """
        A get method to retrieve a list of all the existing instances of the model Book.
        """
        return self.list(request)


class UserCreateAndLoginApiView(CreateAPIView):
    serializer_class = CreateUserSerializer

    def login(self, username, password, request):
        user = authenticate(
            request=self.request,
            username=username,
            password=password
        )
        login(
            request=request,
            user=user
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        username = serializer.validated_data.get('username')
        password = serializer.validated_data.get('password')
        new_user = User(username=username)
        new_user.set_password(password)
        new_user.save()
        Profile.objects.create(user=new_user)
        self.login(username=username, password=password, request=request)

        new_user_serializer = UserSerializer(instance=new_user)
        headers = self.get_success_headers(new_user_serializer.data)
        return Response(new_user_serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class UserDetailApiView(RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsUserOrReadOnly]


class BlogCreateApiView(CreateAPIView):
    serializer_class = BlogCreateSerializer
    permission_classes = [IsAuthenticated]


class BlogDetailApiView(RetrieveUpdateDestroyAPIView):
    serializer_class = BlogDetailSerializer
    permission_classes = [IsAuthenticated, IsBlogsOwner]
    queryset = Blog.objects.select_related('profile').prefetch_related('posts').all()


class BlogListApiView(ListModelMixin, GenericAPIView):
    queryset = Blog.objects.select_related('profile').prefetch_related('posts').all()
    serializer_class = BlogDetailSerializer
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = 'profile__id', 'title', 'profile__user__username'
    filterset_class = BlogFilter

    def get(self, request: HttpRequest) -> Response:
        """
        A get method to retrieve a list of all the existing instances of the model Book.
        """
        return self.list(request)


class PostCreateApiView(CreateModelMixin, GenericAPIView):
    serializer_class = PostCreateSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['profile'] = Profile.objects.get(user=self.request.user)
        return context


class PostUpdateApiView(RetrieveUpdateDestroyAPIView):
    serializer_class = PostDetailSerializer
    permission_classes = [IsPostOwner]
    queryset = Post.objects.select_related('profile').prefetch_related('images').all()

    def check_publish(self, serializer):
        cur_object = self.get_object()
        before_save_published = cur_object.is_published
        serializer.save()
        cur_object = self.get_object()
        if cur_object.is_published and cur_object.is_published != before_save_published:
            cur_object.publish()
        elif not cur_object.is_published and cur_object.is_published != before_save_published:
            cur_object.archive()

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.check_publish(serializer)
        new_serializer = PostDetailSerializer(instance=self.get_object())

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        return Response(new_serializer.data)


class ImageCreateApiView(CreateModelMixin, GenericAPIView):
    serializer_class = ImageCreateSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['profile'] = Profile.objects.get(user=self.request.user)
        return context


class ImageDetailApiView(RetrieveUpdateDestroyAPIView):
    serializer_class = ImageDetailSerializer
    queryset = Image.objects.select_related('post').all()
    permission_classes = [IsImageOwner]


class PostListApiView(ListModelMixin, GenericAPIView):
    serializer_class = PostSerializer
    queryset = Post.objects.select_related('profile', 'blog').prefetch_related('images').all()
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = 'title', 'tag', 'is_published',
    filterset_class = PostFilter

    def get(self, request: HttpRequest) -> Response:
        """
        A get method to retrieve a list of all the existing instances of the model Book.
        """
        return self.list(request)