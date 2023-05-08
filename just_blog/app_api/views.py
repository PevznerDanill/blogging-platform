from rest_framework.permissions import IsAuthenticated
from app_auth.models import Profile
from app_blog.models import Blog, Post, Image
from rest_framework.generics import (
    GenericAPIView,
    RetrieveUpdateDestroyAPIView,
    CreateAPIView,
    RetrieveUpdateAPIView,
)
from rest_framework.mixins import ListModelMixin, CreateModelMixin
from .serializers import (
    ProfileFullSerializer,
    ProfileSerializer,
    BlogCreateSerializer,
    BlogDetailSerializer,
    PostCreateSerializer,
    PostDetailSerializer,
    ImageCreateSerializer,
    ImageDetailSerializer,
    PostSerializer,
)
from django.http import HttpRequest
from rest_framework.response import Response
from .filters import ProfileFilter, PostFilter, BlogFilter
from rest_framework import filters
from django_filters.rest_framework import DjangoFilterBackend
from .permissions import (
    IsBlogsOwner,
    IsPostOwner,
    IsImageOwner,
    IsProfile,
    IsProfileOwnerOrReadOnly
)
from django.db.models import F
from rest_framework.parsers import MultiPartParser, FormParser


class ProfileListApiView(ListModelMixin, GenericAPIView):
    """
    Returns a list of all profiles. Allows filtering by the fields
    username, first_name, last_name, email (these four belong to the related User instance)
    and the field birthday which corresponds to the age field of the Profile model.
    """
    queryset = Profile.objects.select_related('user').prefetch_related('blogs', 'posts').all()
    serializer_class = ProfileFullSerializer
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = 'user__username', 'user__first_name', 'user__last_name', 'user__email', 'age'
    filterset_class = ProfileFilter

    def get(self, request: HttpRequest) -> Response:
        """
        A get method to retrieve a list of all the existing instances of the model Profile.
        """
        return self.list(request)


class ProfileCreateApiView(CreateAPIView):
    """
    An api view to create a new profile instance.
    The avatar field is defined in the serializer as an ImageField, and it is possible to
    upload a new file.

    One User can have only one Profile, so it is impossible to create a new Profile instance
    if the current user already has one.
    """
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated, IsProfile]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request: HttpRequest, *args, **kwargs) -> Response:
        """
        A post method to create a new Profile instance.
        The fields for a new profile are bio, age and avatar. None of them are required.
        """
        return self.create(request, *args, **kwargs)


class ProfileUpdateApiView(RetrieveUpdateAPIView):
    """
    An api view to update the retrieved Profile instance by its id.
    If the user hasn't logged in or the authenticated user is not related
    to the retrieved Profile instance, only safe methods are allowed.
    """
    queryset = Profile.objects.select_related('user')
    serializer_class = ProfileSerializer
    permission_classes = [IsProfileOwnerOrReadOnly]

    def get(self, request: HttpRequest, *args, **kwargs) -> Response:
        """
        A get method to retrieve a Profile instance.
        """
        return self.retrieve(request, *args, **kwargs)

    def put(self, request: HttpRequest, *args, **kwargs) -> Response:
        """
        A post method to update the retrieved Profile instance.
        The fields to update are bio, age, avatar.
        """
        return self.update(request, *args, **kwargs)

    def patch(self, request: HttpRequest, *args, **kwargs) -> Response:
        """
        A patch method to partially update the retrieved Profile instance.
        The fields to update are bio, age, avatar.
        """
        return self.partial_update(request, *args, **kwargs)


class BlogCreateApiView(CreateAPIView):
    """
    An api view to create a new Blog instance.
    Only an authenticated user can create a new Blog instance.
    """
    serializer_class = BlogCreateSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request: HttpRequest, *args, **kwargs) -> Response:
        """
        A post method to create a new Blog instance. The fields to fill are title and description.
        """
        return self.create(request, *args, **kwargs)


class BlogDetailApiView(RetrieveUpdateDestroyAPIView):
    """
    An api view to retrieve, update or destroy a Blog instance.
    To perform unsafe methods, the retrieved Blog instance should belong to the current
    Profile instance.
    """
    serializer_class = BlogDetailSerializer
    permission_classes = [IsBlogsOwner]
    queryset = Blog.objects.select_related('profile').prefetch_related('posts').all()

    def get(self, request: HttpRequest, *args, **kwargs) -> Response:
        """
        A get method to retrieve a Blog instance by its id. The fields in the response are
        title, description, posts, profile.
        The posts field contains a hyperlink to the details of the post.
        """
        return self.retrieve(request, *args, **kwargs)

    def put(self, request: HttpRequest, *args, **kwargs) -> Response:
        """
        A put method to update the retrieved Blog instance.
        The fields to change are title and description.
        """
        return self.update(request, *args, **kwargs)

    def patch(self, request: HttpRequest, *args, **kwargs) -> Response:
        """
        A patch method to partially update the retrieved Blog instance.
        The fields to change are title and description.
        """
        return self.partial_update(request, *args, **kwargs)

    def delete(self, request: HttpRequest, *args, **kwargs) -> Response:
        """
        A delete method to destroy the retrieved Blog instance.
        """
        return self.destroy(request, *args, **kwargs)


class BlogListApiView(ListModelMixin, GenericAPIView):
    """
    An api view to return a list of the model Blog instances.
    Can be filtered by the username of the user which has the Profile instance
    related to the blog, and the title of the Blog instance.
    The search can be performed by the same fields plus the id of the Profile instance
    related to the blog.
    """
    queryset = Blog.objects.select_related('profile').prefetch_related('posts').all()
    serializer_class = BlogDetailSerializer
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = 'profile__id', 'title', 'profile__user__username'
    filterset_class = BlogFilter

    def get(self, request: HttpRequest) -> Response:
        """
        A get method to retrieve a list of all the existing instances of the model Blog.
        The fields for every object of the list are:
        id, title, description, posts and profile.
        The posts field is represented as list of hyperlinks.
        The profile field contains its fields id and username (username of the related user).
        """
        return self.list(request)


class PostCreateApiView(CreateModelMixin, GenericAPIView):
    """
    An api view to create a new Post instance.
    Available only for the authenticated users.
    """
    serializer_class = PostCreateSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request: HttpRequest, *args, **kwargs) -> Response:
        """
        A post method to create a new Post instance.
        The fields to fill are title, tag, blog (id: int) and content.
        """
        return self.create(request, *args, **kwargs)

    def get_serializer_context(self):
        """
        Returns a context for the serializer, with the current Profile instance in it.
        Serves to filter the possible blogs to choose between.
        """
        context = super().get_serializer_context()
        context['profile'] = Profile.objects.get(user=self.request.user)
        return context


class PostUpdateApiView(RetrieveUpdateDestroyAPIView):
    """
    An api view to retrieve, update and destroy a Post instance.
    If the post is not published, only its owner can see it.
    If it is, the safe methods are available to any user.
    The owner of the post can perform all the available methods.
    """
    serializer_class = PostDetailSerializer
    permission_classes = [IsPostOwner]
    queryset = Post.objects.select_related('profile').prefetch_related('images').all()

    def check_publish(self, serializer: PostDetailSerializer) -> None:
        """
        If the user change to True the field is_published, performs the publish() method
        of the Post instance.
        If the user change to False the field is_published, performs the archive() method
        of the Post instance.
        """
        cur_object = self.get_object()
        before_save_published = cur_object.is_published
        serializer.save()
        cur_object = self.get_object()
        if cur_object.is_published and cur_object.is_published != before_save_published:
            cur_object.publish()
        elif not cur_object.is_published and cur_object.is_published != before_save_published:
            cur_object.archive()

    def update(self, request: HttpRequest, *args, **kwargs) -> Response:
        """
        Overrides the default update method, adding to it the call to the self.check_publish(serializer)
        method.
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.check_publish(serializer)
        new_serializer = PostDetailSerializer(instance=self.get_object())

        if getattr(instance, '_prefetched_objects_cache', None):
            instance._prefetched_objects_cache = {}

        return Response(new_serializer.data)

    def get(self, request: HttpRequest, *args, **kwargs) -> Response:
        """
        A method to retrieve a Post instance by its id.
        The fields in the response are:
        id, title, tag, blog, profile, content,
        created_at, is_published, published_at, images.
        The images field is a nested list with the id and title of every image.
        """
        return self.retrieve(request, *args, **kwargs)

    def put(self, request: HttpRequest, *args, **kwargs) -> Response:
        """
        A put method to update the retrieved Post instance.
        The fields that can be updated are:
        title, tag, content, and is_published.
        """
        return self.update(request, *args, **kwargs)

    def patch(self, request: HttpRequest, *args, **kwargs) -> Response:
        """
        A patch method to partially update the retrieved Post instance.
        The fields that can be updated are:
        title, tag, content, and is_published.
        """
        return self.partial_update(request, *args, **kwargs)

    def delete(self, request: HttpRequest, *args, **kwargs) -> Response:
        """
        A delete method to destroy the retrieved Post instance.
        """
        return self.destroy(request, *args, **kwargs)


class ImageCreateApiView(CreateModelMixin, GenericAPIView):
    """
    An api view to create a new instance of the Image model.
    Available only for the authenticated users.
    """
    serializer_class = ImageCreateSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request: HttpRequest, *args, **kwargs) -> Response:
        """
        A post method to create a new instance of the Image model.
        The fields to fill are title, image and post (id: int).
        """
        return self.create(request, *args, **kwargs)

    def get_serializer_context(self):
        """
        Returns a context for the serializer with the current Profile instance to filter
        only those posts related to the Profile.
        """
        context = super().get_serializer_context()
        context['profile'] = Profile.objects.get(user=self.request.user)
        return context


class ImageDetailApiView(RetrieveUpdateDestroyAPIView):
    """
    An api view to retrieve, update or destroy a Image instance.
    The unsafe methods are available only for the user with the Profile instance
    related to the retrieved Image instance.
    """
    serializer_class = ImageDetailSerializer
    queryset = Image.objects.select_related('post').annotate(owner=F('post__profile')).all()
    permission_classes = [IsImageOwner]
    parser_classes = (MultiPartParser, FormParser)

    def get(self, request: HttpRequest, *args, **kwargs) -> Response:
        """
        A get method to retrieve an Image instance by its id.
        The fields in the response are:
        id, title, image and post.
        """
        return self.retrieve(request, *args, **kwargs)

    def put(self, request: HttpRequest, *args, **kwargs) -> Response:
        """
        A put method to update the retrieved Image instance.
        The fields that can be changed are title and image.
        Requires type multipart.
        """
        return self.update(request, *args, **kwargs)

    def patch(self, request: HttpRequest, *args, **kwargs) -> Response:
        """
        A patch method to update the retrieved Image instance.
        The fields that can be changed are title and image.
        Requires type multipart.
        """
        return self.partial_update(request, *args, **kwargs)

    def delete(self, request: HttpRequest, *args, **kwargs) -> Response:
        """
        A delete method to destroy the retrieved Image instance.
        """
        return self.destroy(request, *args, **kwargs)


class PostListApiView(ListModelMixin, GenericAPIView):
    """
    An api view that returns a list of the published Post instances.
    Can be filtered by the username of the User instance related to the Profile instance related to the Post,
    by post's tag and its title.
    """
    serializer_class = PostSerializer
    queryset = Post.objects.select_related('profile', 'blog').prefetch_related('images').filter(is_published=True)
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = 'title', 'tag',
    filterset_class = PostFilter

    def get(self, request: HttpRequest) -> Response:
        """
        A get method to retrieve a list of all the published instances of the model Post.
        Every object of the list contains
        id, title, tag, content, created_at, is_published,
        blog, profile and images fields.
        The blog field contains its own fields id and title.
        The profile field contains its owns fields id and username (username of the related User instance).
        The images field represents a nested list with id and title of every image.
        """
        return self.list(request)
