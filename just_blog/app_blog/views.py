from django.core.exceptions import PermissionDenied
from django.shortcuts import render, reverse, redirect, get_object_or_404, get_list_or_404
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView
from .models import Blog, Post, Image
from app_auth.models import Profile
from .forms import BlogForm, PostForm, PostFileForm
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from csv import reader
from django.http import HttpRequest, HttpResponseRedirect, Http404, HttpResponse
from app_auth.utils import get_profile_for_context
from .utils import save_post_from_csv
from django.utils.translation import gettext_lazy as _
from django.db.models import F, Q, Prefetch, QuerySet
from typing import Union, Dict, List, Optional
from django.views import View
from django.forms.forms import Form
from django.core.paginator import Paginator, Page


class UserBlogListView(ListView):
    """
    A view for the list of blogs of the given Profile instance.
    """
    template_name = 'app_blog/user_blog_list.html'
    context_object_name = 'blogs'

    def setup(self, request: HttpRequest, *args, **kwargs) -> None:
        """
        Overrides the default setup method to get the pk: int passed to the kwargs.
        """
        super().setup(request, *args, **kwargs)
        self.profile_pk: int = self.kwargs.get('pk')

    def get_queryset(self) -> Optional[QuerySet]:
        """
        Takes the self.profile_pk to filter the Blog objects.
        """
        try:
            blogs = get_list_or_404(
                Blog.objects.select_related('profile').
                prefetch_related(Prefetch('posts', queryset=Post.objects.prefetch_related('images'))),
                profile__pk=self.profile_pk
            )
        except Http404 as exc:
            blogs = None
        return blogs

    def get_context_data(self, *, object_list=None, **kwargs) -> Dict[str, Union[bool, List[Blog], Profile, View]]:
        """
        Uses the pk argument passed in the kwargs to retrieve the Profile instance.
        If the current user is authenticated, retrieves its Profile instance.
        """
        context = super().get_context_data(object_list=None, **kwargs)
        if self.request.user.is_authenticated:
            context['profile'] = get_profile_for_context(self.request)
        context['cur_profile'] = get_object_or_404(Profile.objects.select_related('user'), pk=self.profile_pk)
        return context


class BlogCreateView(LoginRequiredMixin, CreateView):
    """
    A view for the process of Blog instance creation.
    """
    form_class = BlogForm
    template_name = 'app_blog/blog_new.html'

    def setup(self, request: HttpRequest, *args, **kwargs) -> None:
        """
        Overrides the default setup method to initiate self.profile attribute, which is a
        Profile instance related to the User instance saved in request.user.
        If the user isn't authenticated, redirects to the Login form.
        """
        super().setup(request, *args, **kwargs)
        if request.user.is_authenticated:
            self.profile: Profile = get_profile_for_context(request)

    def get_context_data(self, **kwargs) -> Dict[str, Union[Profile, View, BlogForm]]:
        """
        Retrieves the Profile instance saved in self.profile attribute and adds it
        to the context.
        """
        context = super().get_context_data(**kwargs)
        context['profile'] = self.profile
        return context

    def form_valid(self, form: BlogForm) -> HttpResponseRedirect:
        """
        Adds the Profile instance saved in self.profile attribute to the form.
        """
        form.instance.profile = self.profile
        self.object = form.save()
        return super().form_valid(form)

    def get_success_url(self) -> str:
        return reverse('app_blog:blog_detail', kwargs={'pk': self.object.pk})


class BlogDetailView(DetailView):
    """
    A view to display the details of a Blog instance.
    """
    queryset = (
        Blog.objects.select_related('profile').prefetch_related('posts')
    )
    template_name = 'app_blog/blog_detail.html'
    context_object_name = 'blog'

    def get_context_data(self, **kwargs) -> Dict[str, Union[Blog, View, Profile, QuerySet]]:
        """
        Retrieves the Profile instance saved in self.profile attribute and adds it
        to the context.
        Also adds to it Post instances related to the current Blog instance.
        """
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            context['profile'] = get_profile_for_context(self.request)
        context['posts'] = Post.objects.select_related('blog', 'profile').\
            prefetch_related('images').filter(blog=context['blog'])
        return context


class BlogDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """
    A view for the process of removing a Blog instance.
    """
    model = Blog
    template_name = 'app_blog/blog_delete.html'
    context_object_name = 'blog'

    def setup(self, request: HttpRequest, *args, **kwargs) -> None:
        """
        Overrides the default setup method to initiate self.cur_profile attribute, which is a
        Profile instance related to the User instance saved in request.user.
        Declares self.object attribute.
        """
        super().setup(request, *args, **kwargs)
        if request.user.is_authenticated:
            self.cur_profile: Profile = get_profile_for_context(request)
        self.object = self.get_object()

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """
        Overrides the default get method, deleting from it declaration of the
        self.object attribute, as it was declared before in self.setup() method.
        """
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)

    def test_func(self) -> bool:
        """
        Checks if the current Profile instance saved in self.cur_profile
        is the same as the Profile instance related to the Blog object with the passed pk.
        """
        return self.cur_profile == self.object.profile

    def get_success_url(self) -> str:
        """
        Generates a reverse link to the app_blog:user_blog_list,
        with the pk argument corresponding to the Profile instance's pk.
        """
        return reverse('app_blog:user_blog_list', kwargs={'pk': self.cur_profile.pk})

    def get_context_data(self, **kwargs) -> Dict[str, Union[Blog, Form, View, Profile]]:
        """
        Adds to the context Profile instance saved in self.cur_profile.
        """
        context = super().get_context_data(**kwargs)
        context['profile'] = self.cur_profile
        return context


class PostDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """
    A view for the process of removing the retrieved Post instance.
    """
    model = Post
    template_name = 'app_blog/post_delete.html'
    context_object_name = 'post'

    def setup(self, request: HttpRequest, *args, **kwargs) -> None:
        """
        Overrides the default setup method to initiate self.cur_profile attribute, which is a
        Profile instance related to the User instance saved in request.user.
        Declares self.object attribute.
        """
        super().setup(request, *args, **kwargs)
        if request.user.is_authenticated:
            self.profile: Profile = get_profile_for_context(self.request)
        self.object = self.get_object()

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """
        Overrides the default get method, deleting from it declaration of the
        self.object attribute, as it was declared before in self.setup() method
        """

        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)

    def test_func(self) -> bool:
        """
        Checks if the current Profile instance saved in self.cur_profile
        is the same as the Profile instance related to the Post object with the passed pk.
        """
        return self.profile == self.object.profile

    def get_success_url(self) -> str:
        """
        Generates a link to the app_blog:blog_detail with the pk: int saved in self.blog_pk
        """
        return reverse('app_blog:blog_detail', kwargs={'pk': self.blog_pk})

    def form_valid(self, form: Form) -> HttpResponseRedirect:
        """
        Overrides the default form_valid method.
        Takes the retrieved Post instance that is being deleted, and saves the pk of its
        related Blog instance in self.blog_pk attribute.
        """
        self.blog_pk: int = self.object.blog.pk
        result = super().form_valid(form)
        return result

    def get_context_data(self, **kwargs) -> Dict[str, Union[Post, Form, View]]:
        """
        Adds to the context the Profile instance saved in self.profile attribute.
        """
        context = super().get_context_data(**kwargs)
        context['profile'] = self.profile
        return context


class PostCreateView(UserPassesTestMixin, CreateView):
    """
    A view for the creation of a new Post instance.
    """

    form_class = PostForm
    form_class_1 = PostFileForm
    template_name = 'app_blog/post_new.html'
    queryset = (
        Post.objects.select_related('blog').prefetch_related('images')
    )

    def setup(self, request: HttpRequest, *args, **kwargs) -> None:
        """
        If the user is authenticated, initiates a self.profile attribute that saves the
        Profile instance related to the User instance stored in the request.user.
        If user isn't authenticated, redirects to the Login Form.
        Also retrieves the Blog instance getting it by its id and saves it to self.blog attribute.
        """
        super().setup(request, *args, **kwargs)
        if request.user.is_authenticated:
            self.profile: Profile = get_profile_for_context(request)
        self.blog = get_object_or_404(Blog.objects.select_related('profile'), pk=self.kwargs.get('pk'))

    def test_func(self) -> bool:
        """
        Checks if the blog where a new post is being creating (saved in self.blog attribute) has the same profile
        field as the Profile instance saved in self.profile attribute.
        """
        if self.request.user.is_authenticated:
            return self.blog.profile == self.profile

    def get_success_url(self, new_object: Post = None) -> str:
        """
        Generates a link to the new created post.
        If the new_object is not None, uses its pk to generate the link.
        Otherwise, uses the Post instance saved in self.object attribute.
        """
        if new_object:
            pk = new_object.pk
        else:
            pk = self.object.pk
        return reverse('app_blog:post_detail', kwargs={'pk': pk})

    def form_valid(self, form: PostForm) -> HttpResponseRedirect:
        """
        Adds Blog instance and Profile to the new Post instance's fields and saves it in the self.object attribute.
        Also checks if any images were uploaded and if they were create their new instances,
        passing the new post (self.object) to the post field.
        """
        form.instance.blog = self.blog
        form.instance.profile = self.profile
        self.object = form.save()
        if self.request.FILES:
            images = self.request.FILES.getlist('images')
            for img in images:
                image_instance = Image(title=img.name, image=img, post=self.object)
                image_instance.save()
        return super().form_valid(form)

    def get_context_data(self, **kwargs) -> Dict[str, Union[PostForm, PostFileForm, View, Profile]]:
        """
        Adds the Profile instance of the current user, PostFileForm and PostForm to the context.
        """
        context = super().get_context_data(**kwargs)
        context['profile'] = self.profile
        context['form'] = self.get_form()
        context['form_1'] = self.form_class_1
        return context

    def get_invalid_context(self) -> HttpResponse:
        """
        Returns HttpResponse with the template defined in self.template_name and a new context,
        which contains an error message.
        """
        context = {
            'form': self.get_form(),
            'form_1': self.form_class_1,
            'error': _('The file you have just tried to upload is invalid'),
            'profile': self.profile,
        }
        return render(self.request, self.template_name, context=context)

    def post(self, request: HttpRequest, *args, **kwargs) -> Union[HttpResponseRedirect, HttpResponse]:
        """
        Overrides the default post method.
        If the PostForm is valid, returns self.form_valid(form), as usual.
        If the PostFileForm is valid, creates a new Post instance from a cvs file.
        During the creation also checks if the uploaded file is correct. Ig not, returns
        the self.get_invalid_context() method.
        If none of the forms are valid, returns the self.form_invalid(form) method.
        """
        form = self.get_form()
        form_2 = self.form_class_1(request.POST, request.FILES)
        profile = get_profile_for_context(self.request)

        if form.is_valid():
            return self.form_valid(form)

        elif form_2.is_valid():
            try:
                csv_file = form_2.cleaned_data['file'].read()
                csv_file_str = csv_file.decode('utf-8').splitlines()
            except Exception:
                return self.get_invalid_context()
            try:
                csv_reader = reader(csv_file_str, delimiter=',', quotechar='"')
                result = save_post_from_csv(
                    csv_reader=csv_reader,
                    profile=profile,
                    kwargs=self.kwargs
                    )
                if not result:
                    return self.get_invalid_context()

            except IndexError:
                csv_reader = reader(csv_file_str, delimiter=';', quotechar='"')
                result = save_post_from_csv(
                    csv_reader=csv_reader,
                    profile=profile,
                    kwargs=self.kwargs
                )
                if not result:
                    return self.get_invalid_context()
            return redirect(self.get_success_url(new_object=result))
        else:
            self.object = None
            return self.form_invalid(form)


class PostDetailView(UserPassesTestMixin, DetailView):
    """
    A view class for  details of a Post instance.
    """
    queryset = (
        Post.objects.select_related('blog', 'profile').
        prefetch_related('images').
        annotate(blog_pk=F('blog__pk')).
        annotate(profile_pk=F('profile__pk')).
        annotate(profile_name=F('profile__user__username'))
    )
    template_name = 'app_blog/post_detail.html'
    context_object_name = 'post'

    def setup(self, request: HttpRequest, *args, **kwargs) -> None:
        """
        Overrides the default setup method. Initiates a new attribute self.profile where saves
        the Profile instance related to the request.user, providing he is authenticated.
        Declares the self.object attribute.
        """
        super().setup(request, *args, **kwargs)
        if request.user.is_authenticated:
            self.profile = get_profile_for_context(request)
        self.object = self.get_object()

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """
        Overrides the default self.get() method, deleting from it
        the declaration of the self.object attribute, as it was declared
        before in self.setup().
        """
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)

    def test_func(self) -> bool:
        """
        Checks if the user is the owner of the requested post, if he is the superuser or if the post is published.
        Otherwise returns false.
        """
        cur_profile = None
        if self.request.user.is_authenticated:
            cur_profile = self.profile
        return self.object.is_published or cur_profile == self.object.profile or self.request.user.is_superuser

    def get_context_data(self, **kwargs) -> Dict[str, Union[Post, Profile, View]]:
        """
        Adds Profile instance saved in the request.user if he is authenticated.
        """
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            context['profile'] = self.profile
        return context


class BlogEditView(UserPassesTestMixin, UpdateView):
    """
    A view for the blog editing.
    """
    form_class = BlogForm
    queryset = (
        Blog.objects.select_related('profile')
    )
    template_name = 'app_blog/blog_edit.html'
    context_object_name = 'blog'

    def setup(self, request: HttpRequest, *args, **kwargs) -> None:
        """
        If the user is authenticated, retrieves its related Profile instance
        and saves it to the self.profile attribute.
        Declares self.object attribute.
        """
        if request.user.is_authenticated:
            self.profile = get_profile_for_context(request)
        super().setup(request, *args, **kwargs)
        self.object = self.get_object(self.queryset)

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """
        Overrides the default self.get() method deleting
        from it the declation of the self.object attribute, as it was
        declared before in self.setup() method.
        """
        return self.render_to_response(self.get_context_data())

    def test_func(self) -> bool:
        """
        Checks if the Profile instance retrieved from the related User instance (from the authenticated
        current user) is the same as the profile field of the Blog object that is being
        edited.
        """
        if self.request.user.is_authenticated:
            return self.object.profile == self.profile

    def get_context_data(self, **kwargs) -> Dict[str, Union[Blog, BlogForm, View, Profile]]:
        """
        Adds Profile instance to the context.
        """
        context = super().get_context_data(**kwargs)
        context['profile'] = self.profile
        return context

    def get_success_url(self) -> str:
        """
        Generates a link back to the edited blog.
        """
        return reverse('app_blog:blog_detail', kwargs={'pk': self.object.pk})


class PostEditView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """
    A view for the editing of the retrieved post.
    """
    queryset = (
        Post.objects.select_related('blog', 'profile').prefetch_related('images')
    )
    template_name = 'app_blog/post_edit.html'
    form_class = PostForm

    def setup(self, request: HttpRequest, *args, **kwargs) -> None:
        """
        If the user is authenticated, retrieves its related Profile instance
        and saves it to the self.profile attribute.
        Declares the self.object attribute and self.images, which stores a images
        instances related to the retrieved post.
        """
        if request.user.is_authenticated:
            self.profile = get_profile_for_context(request)
        super().setup(request, *args, **kwargs)
        self.object = self.get_object()
        self.images = get_list_or_404(Image.objects.select_related('post'), post=self.object)

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """
        Overrides the default self.get() method deleting from it
        the declaration of the self.object attribute, as it was declared before in
        self.setup() method.
        """
        return self.render_to_response(self.get_context_data())

    def test_func(self) -> bool:
        """
        Checks if the profile field of the retrieved Post instance is the same as
        the Profile instance saved in self.profile.
        Also returns True if the user is superuser.
        """
        if self.request.user.is_authenticated:
            return self.object.profile == self.profile or self.request.user.is_superuser

    def get_context_data(self, **kwargs) -> Dict[str, Union[Post, PostForm, QuerySet, View, Profile]]:
        """
        Adds self.profile and images related to the retrieved Post instance to the context.
        """
        context = super().get_context_data(**kwargs)
        context['profile'] = self.profile
        context['images'] = self.images
        return context

    def get_success_url(self) -> str:
        """
        Generates a link to the edited post details.
        """
        return reverse('app_blog:post_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form: PostForm):
        """
        Saves the posted form.
        Checks if the user marked checkbox inputs with the saved ids of the already uploaded images.
        If marked, deletes them.
        Also checks if there were new images uploaded and if they were, creates new Image instances.
        """
        self.object = form.save()
        for current_image in self.images:
            if self.request.POST.get(str(current_image.pk)) == 'on':
                current_image.delete()
        if self.request.FILES:
            images = self.request.FILES.getlist('images')
            for img in images:
                self.object.images.create(title=img.name, image=img)
        return super().form_valid(form)


@login_required
def publish_or_archive(request: HttpRequest, pk: int) -> HttpResponseRedirect:
    """
    Checks the current flag in the is_published field of the Post instance with the
    passed pk and if it is True, performs the method archive() of the Post model.
    If it is False, performs its method publish().
    Then redirects to the page of the retrieved post.
    """
    cur_post = get_object_or_404(Post.objects.select_related('profile'), pk=pk)
    if cur_post.profile != get_profile_for_context(request):
        raise PermissionDenied
    if cur_post.is_published:
        cur_post.archive()
    else:
        cur_post.publish()
    return redirect(reverse('app_blog:post_detail', kwargs={'pk': pk}))


class LatestPostsView(ListView):
    """
    A view to display the latest published posts.
    """
    queryset = (
        Post.objects.select_related('blog', 'profile').prefetch_related('images').
        filter(is_published=True).order_by('-published_at')
    )
    paginate_by = 5
    context_object_name = 'posts'

    template_name = 'app_blog/latest_posts.html'

    def get_context_data(self, *, object_list=None, **kwargs) -> \
            Dict[str, Union[Paginator, Page, bool, QuerySet, View, Profile]]:
        """
        Adds to the context Profile instance related to the User instance saved
        in the request.user and Profile instances related to the retrieved posts.
        """
        context = super().get_context_data(object_list=None, **kwargs)
        if self.request.user.is_authenticated:
            context['profile'] = get_profile_for_context(self.request)
        profiles = Profile.objects.select_related('user').\
            prefetch_related('blogs', 'posts').filter(Q(posts__in=context['posts']))
        context['profiles'] = profiles

        return context

